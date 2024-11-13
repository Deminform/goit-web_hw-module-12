from fastapi import HTTPException, Depends, status, Query, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from src.contacts import repository as repo_contacts
from src.contacts.schemas import ContactSchema, ContactResponseSchema, ContactUpdateSchema

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get('/', response_model=list[ContactResponseSchema])
async def get_contacts_upcoming_birthday(
        limit: int = Query(10, ge=10, le=100),
        offset: int = Query(None, ge=0),
        days_to_birthday: int = Query(None, ge=0, le=365, description='None - for disable filter by birthday'),
        email: str = Query(None, description='Full or part of an email'),
        fullname: str = Query(None, description='Full or part of a name'),
        db: AsyncSession = Depends(get_db)):
    contacts = await repo_contacts.get_contacts(
        limit=limit,
        skip=offset,
        days=days_to_birthday,
        email=email,
        fullname=fullname,
        db=db)
    return contacts


@router.get('/{contact_id}', response_model=ContactResponseSchema)
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact = await repo_contacts.get_contact_by_id(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post('/', response_model=ContactResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db)):
    contact = await repo_contacts.create_contact(body, db)
    return contact


@router.put('/{contact_id}')
async def update_contact(body: ContactUpdateSchema, contact_id: int, db: AsyncSession = Depends(get_db)):
    contact = await repo_contacts.update_contact(contact_id=contact_id, body=body, db=db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete('/{contact_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact = await repo_contacts.delete_contact(contact_id, db)
    return contact
