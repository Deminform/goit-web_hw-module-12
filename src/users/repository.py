from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from database.db import get_db
from src.users.models import User, Role
from src.users.schemas import UserSchema, RoleEnum


async def get_users_by_email(email: str, db: AsyncSession = Depends(get_db())):
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db())):
    query = select(Role.id).where(Role.name == RoleEnum.USER.value)
    result = await db.execute(query)
    user_role_id = result.scalar_one_or_none()

    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)

    new_user = User(**body.model_dump(), avatar=avatar, role_id=user_role_id)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession = Depends(get_db())):
    user.refresh_token = token
    await db.commit()


async def verify_email(email: str, db: AsyncSession):
    user = await get_users_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    user = await get_users_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user