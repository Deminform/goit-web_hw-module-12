from fastapi import Depends, Query, APIRouter
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from src.contacts import repository as repo_contacts
from src.contacts.schemas import ContactResponseSchema
from src.services.auth.jwt_auth import auth_service
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

    contacts = await repo_contacts.get_all_contacts(limit, offset, days_to_birthday, email, fullname, db, user_id)
    return contacts
