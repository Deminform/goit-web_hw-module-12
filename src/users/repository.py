from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from database.db import get_db
from src.users.models import User, Role
from src.users.schemas import UserSchema, RoleEnum


async def get_user_by_email(email: str, db: AsyncSession) -> User:
    """
    Retrieve a user by their email address.

    :param email: The email address of the user to retrieve.
    :type email: str
    :param db: The asynchronous database session.
    :type db: AsyncSession

    :return: The user object if found, else None.
    :rtype: User
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def get_user_by_id(user_id: int, db: AsyncSession) -> User:
    stmt = select(User).filter_by(id=user_id)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession):
    """
    Create a new user with the given information.

    :param body: The schema containing user information.
    :type body: UserSchema
    :param db: The asynchronous database session.
    :type db: AsyncSession

    :return: The newly created user object.
    :rtype: User
    """
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


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    Update the refresh token for a user.

    :param user: The user object to update.
    :type user: User
    :param token: The new refresh token or None to clear it.
    :type token: str | None
    :param db: The asynchronous database session.
    :type db: AsyncSession
    """
    user.refresh_token = token
    await db.commit()


async def verify_email(email: str, db: AsyncSession):
    """
    Verify a user's email address.

    :param email: The email address to verify.
    :type email: str
    :param db: The asynchronous database session.
    :type db: AsyncSession
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_user_password(email: str, password: str, db: AsyncSession = Depends(get_db)):
    """
    Update a user's password.

    :param email: The email address of the user.
    :type email: str
    :param password: The new password.
    :type password: str
    :param db: The asynchronous database session (optional).
    :type db: AsyncSession

    :return: None
    """
    user = await get_user_by_email(email, db)
    user.password = password
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession = Depends(get_db)) -> User:
    """
    Update a user's avatar URL.

    :param email: The email address of the user.
    :type email: str
    :param url: The new avatar URL or None to clear it.
    :type url: str | None
    :param db: The asynchronous database session (optional).
    :type db: AsyncSession

    :return: The updated user object.
    :rtype: User
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user