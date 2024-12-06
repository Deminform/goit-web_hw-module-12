from fastapi import HTTPException, Depends, status, Query, APIRouter
from fastapi_cache import FastAPICache
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from conf import messages
from database.db import get_db
from src.contacts import repository as repo_contacts
from src.contacts.repository import is_contact_exist
from src.contacts.schemas import (
    ContactSchema,
    ContactResponseSchema,
    ContactUpdateSchema,
)
from src.services.auth.jwt_auth import auth_service
from src.users.models import User

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/",response_model=list[ContactResponseSchema],
            dependencies=[Depends(RateLimiter(times=60, seconds=60))])
async def get_contacts_by_filters(
    limit: int = Query(10, ge=10, le=100),
    offset: int = Query(0, ge=0),
    days_to_birthday: int = Query(None, ge=0, le=365, description="None - for disable filter by birthday"),
    email: str = Query(None, description="Full or part of an email"),
    fullname: str = Query(None, description="Full or part of a name"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)):
    """
    Retrieve a list of contacts filtered by various criteria.

    :param limit: The maximum number of contacts to retrieve (default 10, between 10 and 100).
    :type limit: int
    :param offset: The number of contacts to skip before starting to collect the result set (default 0).
    :type offset: int
    :param days_to_birthday: Filter contacts by days remaining to their next birthday (optional).
    :type days_to_birthday: int, optional
    :param email: Filter contacts by email or part of an email (optional).
    :type email: str, optional
    :param fullname: Filter contacts by full name or part of a name (optional).
    :type fullname: str, optional
    :param db: Database session dependency.
    :type db: AsyncSession
    :param user: The current authenticated user.
    :type user: User

    :return: List of filtered contacts.
    :rtype: list[ContactResponseSchema]
    """
    contacts = await repo_contacts.get_my_contacts(db, user, limit, offset, days_to_birthday, email, fullname)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponseSchema,
            dependencies=[Depends(RateLimiter(times=60, seconds=60))])
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)):
    """
    Retrieve a contact by its ID.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: Database session dependency.
    :type db: AsyncSession
    :param user: The current authenticated user.
    :type user: User

    :return: The requested contact if found.
    :rtype: ContactResponseSchema

    :raises HTTPException: If the contact is not found, raises a 404 error.
    """
    contact = await repo_contacts.get_contact_by_id(contact_id, db, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.CONTACT_NOT_FOUND
        )
    return contact


@router.post("/", response_model=ContactResponseSchema, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(RateLimiter(times=4, seconds=60))])
async def create_contact(
    body: ContactSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)):
    """
    Create a new contact.

    :param body: The contact data to create.
    :type body: ContactSchema
    :param db: Database session dependency.
    :type db: AsyncSession
    :param user: The current authenticated user.
    :type user: User

    :return: The created contact.
    :rtype: ContactResponseSchema

    :raises HTTPException: If the contact already exists, raises a 409 error.
    """
    result = await is_contact_exist(body.email, body.phone, db, user)
    if result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=messages.CONTACT_ALREADY_EXISTS
        )
    contact = await repo_contacts.create_contact(body, db, user)
    return contact


@router.put("/{contact_id}", response_model=ContactResponseSchema, dependencies=[Depends(RateLimiter(times=4, seconds=60))])
async def update_contact(
    body: ContactUpdateSchema,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)):
    """
    Update an existing contact.

    :param body: The updated contact data.
    :type body: ContactUpdateSchema
    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param db: Database session dependency.
    :type db: AsyncSession
    :param user: The current authenticated user.
    :type user: User

    :return: The updated contact.
    :rtype: ContactResponseSchema

    :raises HTTPException: If the contact is not found, raises a 409 error.
    """
    contact = await repo_contacts.update_contact(contact_id, body, db, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=messages.CONTACT_NOT_FOUND
        )
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(RateLimiter(times=60, seconds=60))])
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)):
    """
    Delete a contact by its ID.

    :param contact_id: The ID of the contact to delete.
    :type contact_id: int
    :param db: Database session dependency.
    :type db: AsyncSession
    :param user: The current authenticated user.
    :type user: User

    :return: The deleted contact.
    :rtype: None

    :raises HTTPException: If the contact is not found, raises a 409 error.
    """
    contact = await repo_contacts.delete_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=messages.CONTACT_NOT_FOUND
        )
    return contact