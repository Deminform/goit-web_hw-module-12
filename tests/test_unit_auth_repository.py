import unittest
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache import FastAPICache
from fastapi_mail import MessageSchema, MessageType
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

from src.services.auth.repository import send_verify_email, send_reset_password_email
from src.users.models import User, Role

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

    @patch('src.services.auth.repository.auth_service')
    @patch('src.services.auth.repository.conf')
    @patch('src.services.auth.repository.FastMail')  # Не используем new_callable=AsyncMock здесь
    async def test_send_verify_email(self, mock_fast_mail, mock_conf, mock_auth_service):
        mock_auth_service.create_email_token.return_value = 'some_token'

        fm_instance = MagicMock()
        fm_instance.send_message = AsyncMock()
        mock_fast_mail.return_value = fm_instance
        mock_host = 'https://testhost.com'
        await send_verify_email(self.user.email, self.user.username, mock_host)
        mock_auth_service.create_email_token.assert_called_once_with({'sub': self.user.email})
        mock_fast_mail.assert_called_once_with(mock_conf)
        fm_instance.send_message.assert_awaited_once()
        sent_args, sent_kwargs = fm_instance.send_message.await_args
        message_arg = sent_args[0]
        template_name_arg = sent_kwargs['template_name']

        self.assertEqual(template_name_arg, 'verify_email.html')
        self.assertEqual(message_arg.subject, 'Confirm your email')
        self.assertEqual(message_arg.recipients, [self.user.email])
        self.assertEqual(
            message_arg.template_body,
            {'host': mock_host, 'username': self.user.username, 'token': 'some_token'}
        )
        self.assertEqual(message_arg.subtype, MessageType.html)

    @patch('src.services.auth.repository.auth_service')
    @patch('src.services.auth.repository.conf')
    @patch('src.services.auth.repository.FastMail')
    @patch('src.services.auth.repository.app_config')
    async def test_send_reset_password_email(self, mock_app_config, mock_fast_mail, mock_conf, mock_auth_service):
        email = self.user.email
        username = self.user.username
        temp_code = '123456'
        host = 'https://testhost.com'
        reset_token = 'some_reset_token'

        mock_auth_service.create_reset_password_token.return_value = reset_token

        mock_app_config.TEMP_CODE_LIFETIME = 3600

        fm_instance = MagicMock()
        fm_instance.send_message = AsyncMock()
        mock_fast_mail.return_value = fm_instance

        await send_reset_password_email(email, username, temp_code, host)

        mock_auth_service.create_reset_password_token.assert_called_once_with(email)
        mock_fast_mail.assert_called_once_with(mock_conf)
        fm_instance.send_message.assert_awaited_once()
        sent_args, sent_kwargs = fm_instance.send_message.await_args
        message_arg = sent_args[0]
        template_name_arg = sent_kwargs['template_name']

        self.assertEqual(message_arg.subject, 'Password reset')
        self.assertEqual(message_arg.recipients, [email])
        self.assertEqual(message_arg.template_body, {
            'host': host,
            'username': username,
            'temp_code': temp_code,
            'expires_at': 3600,
            'token': reset_token
        })
        self.assertEqual(message_arg.subtype, MessageType.html)
        self.assertEqual(template_name_arg, 'get_temp_code.html')
