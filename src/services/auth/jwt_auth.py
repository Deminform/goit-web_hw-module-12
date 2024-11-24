from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from conf.config import app_config
from database.db import get_db
from src.users import repository as user_repository


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)

    oauth2_verify_email_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
    oauth2_reset_password_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/reset_password")

    @staticmethod
    def create_reset_password_token(email: str, expires_delta: Optional[float] = None):
        to_encode = {"sub": email}
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=app_config.TEMP_CODE_LIFETIME)
        to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire, "scope": "reset_password"})
        encoded_token = jwt.encode(to_encode, app_config.JWT_SECRET_KEY, algorithm=app_config.ALGORITHM)
        return encoded_token

    @staticmethod
    async def create_access_token(data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=app_config.TOKEN_LIFETIME)
        to_encode.update({'iat': datetime.now(timezone.utc), 'exp': expire, 'scope': 'access_token'})
        encoded_access_token = jwt.encode(to_encode, app_config.JWT_SECRET_KEY, algorithm=app_config.ALGORITHM)
        return encoded_access_token

    @staticmethod
    async def create_refresh_token(data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=app_config.REFRESH_TOKEN_LIFETIME)
        to_encode.update({'iat': datetime.now(timezone.utc), 'exp': expire, 'scope': 'refresh_token'})
        encoded_refresh_token = jwt.encode(to_encode, app_config.JWT_SECRET_KEY, algorithm=app_config.ALGORITHM)
        return encoded_refresh_token

    @staticmethod
    async def decode_refresh_token(refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, app_config.JWT_SECRET_KEY, algorithms=[app_config.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_verify_email_scheme), db: AsyncSession = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (inner)",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, app_config.JWT_SECRET_KEY, algorithms=[app_config.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user = await user_repository.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        return user

    @staticmethod
    def create_email_token(data: dict):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=app_config.VERIFY_EMAIL_TOKEN_LIFETIME)
        to_encode.update({'iat': datetime.now(timezone.utc), 'exp': expire})
        token = jwt.encode(to_encode, app_config.JWT_SECRET_KEY, algorithm=app_config.ALGORITHM)
        return token

    @staticmethod
    async def get_email_from_token(token: str):
        try:
            payload = jwt.decode(token, app_config.JWT_SECRET_KEY, algorithms=[app_config.ALGORITHM])
            email = payload['sub']
            return email
        except JWTError as err:
            print(err)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail='Invalid email verification token')

    @staticmethod
    async def is_active(token: str):
        jwt.decode(token, app_config.JWT_SECRET_KEY, algorithms=[app_config.ALGORITHM])


auth_service = Auth()
