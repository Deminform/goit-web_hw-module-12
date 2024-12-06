from datetime import date, timedelta

from fastapi_cache.decorator import cache
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from conf.cache import clear_cache, custom_key_builder
from src.contacts.models import Contact
from src.contacts.schemas import ContactSchema, ContactUpdateSchema
from src.users.models import User


async def is_contact_exist(email: str, phone: str, db: AsyncSession, user: User) -> Contact | None:
    stmt = select(Contact).filter_by(email=email, phone=phone, user_id=user.id)
    stmt = await db.execute(stmt)
    stored_contact = stmt.scalar_one_or_none()
    if stored_contact:
        return stored_contact
    return None

async def apply_contact_filters(stmt, days: int = None, email: str = None, fullname: str = None):
    """
    Apply filters to the contact query based on the provided parameters including pagination, upcoming birthdays, email, and fullname.

    :param stmt: The SQL statement to add the filters to.
    :type stmt: SQLAlchemy Select object
    :param limit: The number of contacts to return.
    :type limit: int
    :param skip: The number of contacts to skip.
    :type skip: int
    :param days: How many days ahead to look for future birthdays.
    :type days: int
    :param email: The email of the contact to search for.
    :type email: str
    :param fullname: The full name of the contact to search for.
    :type fullname: str
    :param db: The database session.
    :type db: AsyncSession
    :return: A list of filtered contacts.
    :rtype: List[Contact]
    """
    if fullname:
        stmt = stmt.where(Contact.fullname.ilike(f'%{fullname}%'))
    if email:
        stmt = stmt.where(Contact.email.ilike(f'%{email}%'))
    if days:
        today = date.today()
        end_date = today + timedelta(days=days - 1)

        day_today = today.timetuple().tm_yday
        day_end_date = end_date.timetuple().tm_yday

        if day_end_date >= day_today:  # If the birthday is before the end of the year
            stmt = stmt.where(
                and_(
                    func.date_part('doy', Contact.birthday) >= day_today,
                    func.date_part('doy', Contact.birthday) <= day_end_date
                )
            ).order_by(Contact.birthday)
        else:  # If the birthday is at the beginning of next year
            stmt = stmt.where(
                or_(
                    func.date_part('doy', Contact.birthday) >= day_today,
                    func.date_part('doy', Contact.birthday) <= day_end_date
                )
            ).order_by(Contact.birthday)
    return stmt


async def get_all_contacts(db: AsyncSession, user_id: int = None, limit: int = 10, skip: int = 0, days: int = None, email: str = None, fullname: str = None):
    """
    :param limit: The number of contacts to return
    :type limit: int
    :param skip: The number of contacts to skip
    :type skip: int
    :param days: How many days ahead to look for future birthdays
    :type days: int
    :param email: The email of the user
    :type email: str
    :param fullname: The full name of the user
    :type fullname: str
    :param db: The database session
    :type db: AsyncSession
    :param user_id: The id of the user
    :type user_id: int
    :return: A list of contacts
    :rtype: List[Contact]
    """
    if user_id:
        stmt = select(Contact).filter_by(user_id=user_id)
    else:
        stmt = select(Contact)
    stmt = stmt.offset(skip).limit(limit)
    stmt = await apply_contact_filters(stmt, days, email, fullname)
    result = await db.execute(stmt)
    result = result.scalars().all()
    return result

@cache(expire=1200, namespace='get_my_contacts', key_builder=custom_key_builder)
async def get_my_contacts(db: AsyncSession, user: User, limit: int = 10, skip: int = 0, days: int = None, email: str = None, fullname: str = None):
    """
    Retrieve all contacts associated with the given user, applying filters for pagination, upcoming birthdays, email, and fullname.

    :param limit: The number of contacts to return
    :type limit: int
    :param skip: The number of contacts to skip
    :type skip: int
    :param days: How many days ahead to look for future birthdays
    :type days: int
    :param email: The email of the contact
    :type email: str
    :param fullname: The full name of the contact
    :type fullname: str
    :param db: The database session
    :type db: AsyncSession
    :param user: The user object containing the user's details
    :type user: User
    :return: A list of contacts
    :rtype: List[Contact]
    """
    stmt = select(Contact).filter_by(user_id=user.id)
    stmt = stmt.offset(skip).limit(limit)
    stmt = await apply_contact_filters(stmt, days, email, fullname)
    result = await db.execute(stmt)
    result = result.scalars().all()
    return result


async def get_contact_by_id(contact_id: int, db: AsyncSession, user: User) -> Contact:
    """
    Retrieve a contact by its ID for a given user.

    :param contact_id: The ID of the contact to retrieve
    :type contact_id: int
    :param db: The database session
    :type db: AsyncSession
    :param user: The user object containing the user's details
    :type user: User
    :return: The contact object if found, otherwise None
    :rtype: Contact
    """
    contact = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(contact)
    return contact.scalar_one_or_none()


async def create_contact(body: ContactSchema, db: AsyncSession, user: User) -> Contact:
    """
    Create a new contact for the given user.

    :param body: The data for the new contact
    :type body: ContactSchema
    :param db: The database session
    :type db: AsyncSession
    :param user: The user object containing the user's details
    :type user: User
    :return: The created contact object
    :rtype: Contact
    """
    await clear_cache(user.id)
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdateSchema, db: AsyncSession, user: User):
    """
    Update a contact by id.

    :param contact_id: The id of the contact to update
    :type contact_id: int
    :param body: The update schema for the contact
    :type body: ContactUpdateSchema
    :param db: The database session
    :type db: AsyncSession
    :param user: The user who owns the contact
    :type user: User
    :return: The updated contact or None if not found
    :rtype: Optional[Contact]
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact:
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(contact, key, value)

        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        await clear_cache(user.id)

    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    """
    Delete a contact by id.

    :param contact_id: The id of the contact to delete
    :type contact_id: int
    :param db: The database session
    :type db: AsyncSession
    :param user: The user who owns the contact
    :type user: User
    :return: The deleted contact or None if not found
    :rtype: Optional[Contact]
    """
    await clear_cache(user.id)
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact

