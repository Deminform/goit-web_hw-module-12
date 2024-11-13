from fastapi import HTTPException, Depends, status, Query, APIRouter, Security
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from database.db import get_db
from src.users import repository as repo_users
from src.users.models import User
from src.users.schemas import UserSchema, UserResponseSchema, TokenSchema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
async def signup(body: UserSchema, db: AsyncSession = Depends(get_db)):
    pass
    return {}


@router.post("/login")
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    pass
    return {}


@router.get('/refresh_token')
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(), db: AsyncSession = Depends(get_db)):
    pass
    return {}
