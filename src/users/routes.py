from fastapi import HTTPException, Depends, status, APIRouter, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from src.services.auth.verify_email import send_email
from src.users import repository as user_repository
from src.users.schemas import UserSchema, UserResponseSchema, TokenSchema, RequestEmail
from src.services.auth.jwt_auth import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
get_refresh_token = HTTPBearer()


@router.post("/signup", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def signup(body: UserSchema, bt: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
    exist_user = await user_repository.get_users_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await user_repository.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", response_model=TokenSchema)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await user_repository.get_users_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    return await create_and_update_tokens(user, db)


@router.get('/refresh_token', response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(get_refresh_token),
                        db: AsyncSession = Depends(get_db)):
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await user_repository.get_users_by_email(email, db)
    if user.refresh_token != token:
        await user_repository.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect refresh token")
    return await create_and_update_tokens(user, db)


@router.get('/verify_email/{token}')
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    email = await auth_service.get_email_from_token(token)
    user = await user_repository.get_users_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification failed")
    if user.confirmed:
        return {'message': 'Email is already confirmed'}
    await user_repository.verify_email(email, db)
    return {'message': 'Email confirmed'}


@router.post('/request_verify_email', dependencies=[Depends(RateLimiter(times=1, seconds=60))])
async def request_verify_email(body: RequestEmail, bt: BackgroundTasks, request: Request,
                               db: AsyncSession = Depends(get_db)):
    user = await user_repository.get_users_by_email(body.email, db)
    if user.confirmed:
        return {'message': 'Email is already confirmed'}
    if user:
        bt.add_task(send_email, user.email, user.username, str(request.base_url))
    return {'message': 'Check your email for confirmation'}


async def create_and_update_tokens(user, db):
    new_access_token = await auth_service.create_access_token(data={'sub': user.email})
    new_refresh_token = await auth_service.create_refresh_token(data={'sub': user.email})
    await user_repository.update_token(user, new_refresh_token, db)
    return {'access_token': new_access_token, 'refresh_token': new_refresh_token, 'token_type': 'bearer'}
