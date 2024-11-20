from datetime import datetime
from typing import cast

from fastapi import (
    HTTPException,
    Depends,
    status,
    APIRouter,
    Security,
    BackgroundTasks,
    Request,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from src.services.auth.repository import send_verify_email, send_temp_code
from src.services.temp_code.repository import get_temp_code, create_temp_code, update_temp_code
from src.users import repository as user_repository
from src.users.schemas import UserSchema, UserResponseSchema, TokenSchema, RequestEmailSchema, ResetPasswordSchema
from src.services.auth.jwt_auth import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
get_refresh_token = HTTPBearer()


@router.post(
    "/signup", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserSchema,
    bt: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    exist_user = await user_repository.get_users_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await user_repository.create_user(body, db)
    bt.add_task(send_verify_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", response_model=TokenSchema, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def login(
        body: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    user = await user_repository.get_users_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not confirmed"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    return await create_and_update_tokens(user, db)


@router.get("/refresh_token", response_model=TokenSchema, dependencies=[Depends(RateLimiter(times=1, seconds=60))])
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(get_refresh_token),
    db: AsyncSession = Depends(get_db),
):
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await user_repository.get_users_by_email(email, db)
    if user.refresh_token != token:
        await user_repository.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect refresh token"
        )
    return await create_and_update_tokens(user, db)


@router.get("/verify_email/{token}", dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def verify_email(
        token: str,
        db: AsyncSession = Depends(get_db)
):
    email = await auth_service.get_email_from_token(token)
    user = await user_repository.get_users_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification failed"
        )
    if user.confirmed:
        return {"message": "Email is already confirmed"}
    await user_repository.verify_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/request_verify_email", dependencies=[Depends(RateLimiter(times=1, seconds=60))])
async def request_verify_email(
    body: RequestEmailSchema,
    bt: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await user_repository.get_users_by_email(body.email, db)
    if user.confirmed:
        return {"message": "Email is already confirmed"}
    if user:
        bt.add_task(send_verify_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation"}


@router.post("/request_reset_password", dependencies=[Depends(RateLimiter(times=1, minutes=1))])
async def request_reset_password(
        body: RequestEmailSchema,
        bt: BackgroundTasks,
        request: Request,
        db: AsyncSession = Depends(get_db)):
    temp_code = await create_temp_code(body.email, db, description='Request reset password')
    user = await user_repository.get_users_by_email(body.email, db)
    if user is None:
        return {"message": "User not found"}
    if temp_code:
        bt.add_task(send_temp_code, user.email, user.username, temp_code.temp_code, str(request.base_url))
    return {"message": "Check your email for reset password"}


@router.patch('/reset_password', dependencies=[Depends(RateLimiter(times=1, seconds=3))])
async def reset_password(
        body: ResetPasswordSchema,
        db: AsyncSession = Depends(get_db)):

    if body.password != body.password_check:
        return {"message": "Passwords do not match"}

    user = await user_repository.get_users_by_email(body.email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification failed"
        )

    temp_code = await get_temp_code(body.email, body.temp_code, db)
    if temp_code.expires_at < datetime.now() or temp_code.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code has expired"
        )
    if temp_code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code not found"
        )

    new_password = auth_service.get_password_hash(body.password)
    await user_repository.update_user_password(body.email, new_password, db)
    await update_temp_code(body.email, body.temp_code, db)
    return {"message": "Password updated successfully"}


async def create_and_update_tokens(user, db):
    new_access_token = await auth_service.create_access_token(data={"sub": user.email})
    new_refresh_token = await auth_service.create_refresh_token(
        data={"sub": user.email}
    )
    await user_repository.update_token(user, new_refresh_token, db)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


