from fastapi import HTTPException, Depends, status, Query, APIRouter
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from src.contacts import repository as repo_contacts
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
    offset: int = Query(None, ge=0),
    days_to_birthday: int = Query(None, ge=0, le=365, description="None - for disable filter by birthday"),
    email: str = Query(None, description="Full or part of an email"),
    fullname: str = Query(None, description="Full or part of a name"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)):

    contacts = await repo_contacts.get_contacts(limit, offset, days_to_birthday, email, fullname, db, user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponseSchema,
            dependencies=[Depends(RateLimiter(times=60, seconds=60))])
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)):

    contact = await repo_contacts.get_contact_by_id(contact_id, db, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post("/", response_model=ContactResponseSchema, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(RateLimiter(times=4, seconds=60))])
async def create_contact(
    body: ContactSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)):

    try:
        contact = await repo_contacts.create_contact(body, db, user)
        return contact
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Contact already exists.")


@router.put("/{contact_id}", response_model=ContactResponseSchema, dependencies=[Depends(RateLimiter(times=4, seconds=60))])
async def update_contact(
    body: ContactUpdateSchema,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)):

    contact = await repo_contacts.update_contact(contact_id, body, db, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(RateLimiter(times=60, seconds=60))])
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)):

    contact = await repo_contacts.delete_contact(contact_id, db, user)
    return contact
