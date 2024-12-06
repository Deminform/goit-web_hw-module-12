import unittest
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache import FastAPICache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

from src.users.models import User, Role
from src.users.schemas import UserSchema, RoleEnum
from src.users.repository import (
    get_user_by_email,
    get_user_by_id,
    create_user,
    update_token,
    verify_email,
    update_user_password,
    update_avatar_url,
)

faker = Faker()


class TestUsers(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        FastAPICache.init(InMemoryBackend())
        cls.user = User(
            id=1,
            username='Jason',
            email='jason@example.com',
            password='0000000',
            avatar='https://avatars.com/u/1066798.jpg'
        )
        cls.role = Role(id=2, name='user')

    @classmethod
    def tearDownClass(cls):
        ...

    def setUp(cls):
        cls.session = MagicMock(spec=AsyncSession)

    def tearDown(cls):
        ...

    async def test_get_user_by_email(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mock_result
        result = await get_user_by_email(self.user.email, self.session)
        self.session.execute.assert_called_once()
        executed_query = self.session.execute.call_args[0][0]
        expected_query = select(User).filter_by(email=self.user.email)
        self.assertEqual(str(executed_query), str(expected_query))
        self.assertEqual(result, self.user)

    async def test_get_user_by_id(self):
        mock_user = MagicMock()
        mock_user.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mock_user
        result = await get_user_by_id(self.user.id, self.session)
        executed_query = self.session.execute.call_args[0][0]
        expected_query = select(User).filter_by(id=self.user.id)
        self.assertEqual(str(executed_query), str(expected_query))
        self.assertEqual(result, self.user)

    async def test_create_user(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = self.role
        self.session.execute.return_value = mock_result

        mock_body = MagicMock(spec=UserSchema)
        mock_body.model_dump.return_value = {
            'username': 'Jason',
            'email': 'jason@example.com',
            'password': '0000000'
        }

        result = await create_user(body=mock_body, db=self.session)
        called_query = self.session.execute.await_args[0][0]
        role_query = select(Role.id).where(Role.name == RoleEnum.USER.value)

        self.session.execute.assert_awaited_once()
        self.session.commit.assert_awaited_once()
        self.assertEqual(str(called_query), str(role_query))
        self.assertEqual(result.username, self.user.username)
        self.assertEqual(result.email, self.user.email)

    async def test_update_token(self):
        mock_token = MagicMock()
        mock_token.return_value = 'dfFJjwHVhbwfhbxcGGDS'
        mock_user = MagicMock()
        mock_user.scalar_one_or_none.return_value = self.user
        await update_token(self.user, mock_token, self.session)
        self.session.commit.assert_awaited_once()
        self.assertIsInstance(self.user, User)

    @patch('src.users.repository.get_user_by_email', new_callable=AsyncMock)
    async def test_verify_email(self, mock_get_user_by_email):
        mock_get_user_by_email.return_value = self.user
        self.user.confirmed = False
        await verify_email(self.user.email, self.session)
        mock_get_user_by_email.assert_awaited_once_with(self.user.email, self.session)
        self.session.commit.assert_awaited_once()
        self.assertTrue(self.user.confirmed)

    @patch('src.users.repository.get_user_by_email', new_callable=AsyncMock)
    async def test_update_password(self, mock_get_user_by_email):
        old_password = self.user.password
        mock_get_user_by_email.return_value = self.user
        await update_user_password(self.user.email, 'password', self.session)
        mock_get_user_by_email.assert_awaited_once_with(self.user.email, self.session)
        self.session.commit.assert_awaited_once()
        self.assertNotEqual(old_password, self.user.password)

    @patch('src.users.repository.get_user_by_email', new_callable=AsyncMock)
    async def test_update_avatar_url(self, mock_get_user_by_email):
        old_avatar_url = self.user.avatar
        mock_get_user_by_email.return_value = self.user
        await update_avatar_url(self.user.email, 'new_avatar_url', self.session)
        mock_get_user_by_email.assert_awaited_once_with(self.user.email, self.session)
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once_with(self.user)
        self.assertNotEqual(old_avatar_url, self.user.avatar)
