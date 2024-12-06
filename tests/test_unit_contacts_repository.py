import unittest
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache import FastAPICache
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

from src.contacts.schemas import ContactSchema, ContactUpdateSchema
from src.users.models import User
from src.contacts.models import Contact
from src.contacts.repository import (
    get_my_contacts,
    get_all_contacts,
    get_contact_by_id,
    delete_contact,
    create_contact,
    update_contact,
    apply_contact_filters,
    is_contact_exist
)

faker = Faker()


class TestContacts(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        FastAPICache.init(InMemoryBackend())
        cls.user = User(id=1, email=faker.email(), password=faker.password(length=6))
        cls.contact = Contact(
            id=1,
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            email='jason@example.com',
            phone='123654987',
            birthday=faker.past_datetime(),  # type: ignore
            description=faker.text(),
            user_id=cls.user.id
        )
        cls.body_create = ContactSchema(
            first_name='Test_first_name',
            last_name='Test_last_name',
            email=faker.email(),
            phone=faker.phone_number()[:10],
            birthday='2023-01-01',
            description='Test_description'
        )
        cls.body_update = ContactUpdateSchema(
            phone=faker.phone_number()[:10],
            description='Test_description'
        )

    @classmethod
    def tearDownClass(cls):
        ...

    def setUp(cls):
        cls.session = MagicMock(spec=AsyncSession)


    def tearDown(cls):
        ...


    async def test_is_contact_exist(self):
        mock_contact = MagicMock()
        mock_contact.scalar_one_or_none.return_value = self.contact
        self.session.execute.return_value = mock_contact
        result = await is_contact_exist(self.contact.email, self.contact.phone, db=self.session, user=self.user)
        self.assertEqual(result, self.contact)

    async def test_is_contact_exist_incorrect_data(self):
        mock_contact = MagicMock()
        mock_contact.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mock_contact
        result = await is_contact_exist(self.contact.email, self.contact.phone, db=self.session, user=self.user)
        self.assertNotEqual(result, self.contact)


    @patch('src.contacts.repository.apply_contact_filters')
    async def test_get_my_contacts(self, apply_filters):
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [self.contact]
        self.session.execute.return_value = mock_result
        mock_result.scalars.return_value = mock_scalars
        result = await get_my_contacts(db=self.session, user=self.user)
        apply_filters.assert_awaited_once()
        self.assertEqual(result, [self.contact])


    @patch('src.contacts.repository.apply_contact_filters')
    async def test_get_all_contacts(self, apply_filters):
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [self.contact]
        self.session.execute.return_value = mock_result
        mock_result.scalars.return_value = mock_scalars
        result = await get_all_contacts(db=self.session, user_id=self.user.id)
        apply_filters.assert_awaited_once()
        self.assertEqual(result, [self.contact])


    async def test_get_contact_by_id(self):
        mock_contact = MagicMock()
        mock_contact.scalar_one_or_none.return_value = self.contact
        self.session.execute.return_value = mock_contact
        result = await get_contact_by_id(contact_id=self.contact.id, db=self.session, user=self.user)
        self.assertEqual(result, self.contact)


    @patch('src.contacts.repository.clear_cache', new_callable=AsyncMock)
    async def test_create_contact(self, mock_clear_cache):
        result = await create_contact(body=self.body_create, db=self.session, user=self.user)
        mock_clear_cache.assert_awaited_once_with(self.user.id)
        self.session.add.assert_called_with(result)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(result)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, self.body_create.first_name)
        self.assertEqual(result.last_name, self.body_create.last_name)
        self.assertEqual(result.email, self.body_create.email)
        self.assertEqual(result.phone, self.body_create.phone)
        self.assertEqual(result.birthday, self.body_create.birthday)
        self.assertEqual(result.description, self.body_create.description)


    @patch('src.contacts.repository.clear_cache', new_callable=AsyncMock)
    async def test_update_contact(self, mock_clear_cache):
        mock_contact = MagicMock()
        mock_contact.scalar_one_or_none.return_value = self.contact
        self.session.execute.return_value = mock_contact
        result = await update_contact(contact_id=self.contact.id, body=self.body_update, db=self.session, user=self.user)
        mock_clear_cache.assert_awaited_once_with(self.user.id)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(result)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.phone, self.body_update.phone)
        self.assertEqual(result.description, self.body_update.description)

    @patch('src.contacts.repository.clear_cache', new_callable=AsyncMock)
    async def test_delete_contact(self, mock_clear_cache):
        mock_contact = MagicMock()
        mock_contact.scalar_one_or_none.return_value = self.contact
        self.session.execute.return_value = mock_contact
        result = await delete_contact(contact_id=self.contact.id, db=self.session, user=self.user)
        mock_clear_cache.assert_awaited_once_with(self.user.id)
        self.session.delete.assert_called_once_with(self.contact)
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)

