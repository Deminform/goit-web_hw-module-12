from fastapi import Depends, Query, APIRouter, status, HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from conf import messages
from database.db import get_db
from src.contacts import repository as repo_contacts
from src.contacts.schemas import ContactResponseSchema
from src.services.auth.jwt_auth import auth_service
from src.users.repository import get_user_by_id
from src.users.roles_checker import RoleChecker
from src.users.models import User
from src.users.schemas import RoleEnum


router = APIRouter(prefix="/contacts", tags=["admin options"])
access_to_all_routes = RoleChecker([RoleEnum.ADMIN])


@router.get('/all', response_model=list[ContactResponseSchema],
            dependencies=[Depends(access_to_all_routes), Depends(RateLimiter(times=5, seconds=60))])
async def get_all_contacts_by_filters(
        limit: int = Query(10, ge=10, le=100),
        offset: int = Query(None, ge=0),
        days_to_birthday: int = Query(None, ge=0, le=365, description='None - for disable filter by birthday'),
        email: str = Query(None, description='Full or part of an email'),
        fullname: str = Query(None, description='Full or part of a name'),
        db: AsyncSession = Depends(get_db),
        user_id: int = Query(None, description='Filter contacts by specified user "user id"'),
        user: User = Depends(auth_service.get_current_user)):
    """
    Retrieve a list of contacts based on provided filters.

    :param limit: Maximum number of contacts to retrieve (default: 10, range: 10-100).
    :type limit: int
    :param offset: Number of contacts to skip (default: None, must be >=0).
    :type offset: int, optional
    :param days_to_birthday: Filter contacts by number of days until their birthday (default: None, range: 0-365).
    :type days_to_birthday: int, optional
    :param email: Filter contacts by full or part of an email address (default: None).
    :type email: str, optional
    :param fullname: Filter contacts by full or part of a name (default: None).
    :type fullname: str, optional
    :param db: The database session.
    :type db: AsyncSession
    :param user_id: Filter contacts by specified user's ID (default: None).
    :type user_id: int, optional
    :param user: The currently authenticated user.
    :type user: User

    :return: A list of contacts matching the specified filters.
    :rtype: list[ContactResponseSchema]
    """
    result = await get_user_by_id(user_id, db)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND
        )
    contacts = await repo_contacts.get_all_contacts(db, user_id, limit, offset, days_to_birthday, email, fullname)
    return contacts
