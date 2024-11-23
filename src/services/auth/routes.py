from datetime import datetime
from pathlib import Path

from fastapi import (
    HTTPException,
    Depends,
    status,
    APIRouter,
    Security,
    BackgroundTasks,
    Request, Form,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from src.services.auth.repository import send_verify_email, send_reset_password_email
from src.services.temp_code.repository import get_temp_code, create_temp_code, update_temp_code
from src.users import repository as user_repository
from src.users.schemas import UserSchema, UserResponseSchema, TokenSchema, RequestEmailSchema, ResetPasswordSchema
from src.services.auth.jwt_auth import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])
get_refresh_token = HTTPBearer()
BASE_DIR = Path('.')
templates = Jinja2Templates(directory=BASE_DIR / 'src' / 'templates')

router.mount('/static', StaticFiles(directory=BASE_DIR / 'src' / 'static'), name="static")


@router.post(
    "/signup", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED
)
async def signup(
        body: UserSchema,
        bt: BackgroundTasks,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    exist_user = await user_repository.get_user_by_email(body.email, db)
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
    user = await user_repository.get_user_by_email(body.username, db)
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
    user = await user_repository.get_user_by_email(email, db)
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
    user = await user_repository.get_user_by_email(email, db)
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
    user = await user_repository.get_user_by_email(body.email, db)
    if user.confirmed:
        return {"message": "Email is already confirmed"}
    if user:
        bt.add_task(send_verify_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation"}


@router.get('/reset_password/{token}', response_class=HTMLResponse,
            dependencies=[Depends(RateLimiter(times=1, seconds=3))])
async def reset_password_page(token: str, request: Request):
    email = await auth_service.get_email_from_token(token)
    return templates.TemplateResponse("password-reset.html",
                                      {"request": request,
                                       "page_title": "Reset Password",
                                       "email": email,
                                       "token": token
                                       })


@router.post('/reset_password/{token}', dependencies=[Depends(RateLimiter(times=1, seconds=3))])
async def reset_password(
        token: str,
        request: Request,
        password: str = Form(...),
        password_check: str = Form(...),
        temp_code: str = Form(...),
        db: AsyncSession = Depends(get_db),
):
    email = await auth_service.get_email_from_token(token)

    if password != password_check:
        return templates.TemplateResponse(
            'password-reset.html',
            {
                "page_title": "Reset Password",
                "email": email,
                "token": token,
                "request": request,
                "error": "Passwords do not match"
            }
        )

    temp_code_obj = await get_temp_code(email, temp_code, db)

    if temp_code_obj is None or temp_code_obj.expires_at < datetime.now() or temp_code_obj.used_at is not None:
        return templates.TemplateResponse(
            'password-reset.html',
            {
                "page_title": "Reset Password",
                "email": email,
                "token": token,
                "request": request,
                "error": "Code is invalid or expired"
            }
        )

    new_password = auth_service.get_password_hash(password)

    await user_repository.update_user_password(email, new_password, db)

    temp_code_obj.used_at = datetime.now()
    await db.commit()

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="message", value="Password updated successfully", httponly=True)
    return response


@router.post("/request_reset_password", dependencies=[Depends(RateLimiter(times=1, minutes=1))])
async def request_reset_password(
        body: RequestEmailSchema,
        bt: BackgroundTasks,
        request: Request,
        db: AsyncSession = Depends(get_db)):
    temp_code = await create_temp_code(body.email, db, description='Request reset password')
    user = await user_repository.get_user_by_email(body.email, db)
    if user is None:
        return {"message": "User not found"}
    if temp_code:
        bt.add_task(send_reset_password_email, user.email, user.username, temp_code.temp_code, str(request.base_url))
    return {"message": "Check your email for reset password"}


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
