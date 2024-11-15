from datetime import date, timedelta

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.contacts.models import Contact
from src.contacts.schemas import ContactSchema, ContactUpdateSchema
from src.users.models import User


async def get_contacts(limit: int, skip: int, days: int, email, fullname, db: AsyncSession, user: User):
    stmt = select(Contact).filter_by(user=user)
    if fullname:
        stmt = await get_contact_by_name(stmt, fullname)
    if email:
        stmt = await get_contact_by_email(stmt, email)
    if days:
        stmt = await get_contact_for_upcoming_birthday(stmt, days)

    stmt = stmt.offset(skip).limit(limit)

    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact_by_id(contact_id: int, db: AsyncSession, user: User):
    contact = select(Contact).filter_by(id=contact_id, user=user)
    if contact is None:
        return None
    contact = await db.execute(contact)
    return contact.scalar_one_or_none()


async def get_all_contacts(limit: int, skip: int, db: AsyncSession):
    contacts = select(Contact).offset(skip).limit(limit)

    contact = await db.execute(contacts)
    return contact.scalars().all()


async def create_contact(body: ContactSchema, db: AsyncSession, user: User):
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    if contact is None:
        return None

    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdateSchema, db: AsyncSession, user: User):
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact is None:
        return None

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(contact, key, value)

    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def get_contact_by_name(stmt, contact_fullname: str):
    return stmt.where(Contact.fullname.ilike(f'%{contact_fullname}%'))


async def get_contact_by_email(stmt, email: str):
    return stmt.where(Contact.email.ilike(f'%{email}%'))


# local function for get contact by birthday
async def get_contact_for_upcoming_birthday(stmt, days: int):
    today = date.today()
    end_date = today + timedelta(days=days - 1)

    day_today = today.timetuple().tm_yday
    day_end_date = end_date.timetuple().tm_yday

    if day_end_date >= day_today:  # If the birthday is before the end of the year
        return stmt.where(
            and_(
                func.date_part('doy', Contact.birthday) >= day_today,
                func.date_part('doy', Contact.birthday) <= day_end_date
            )
        ).order_by(Contact.birthday)
    else:  # If the birthday is at the beginning of next year
        return stmt.where(
            or_(
                func.date_part('doy', Contact.birthday) >= day_today,
                func.date_part('doy', Contact.birthday) <= day_end_date
            )
        ).order_by(Contact.birthday)


