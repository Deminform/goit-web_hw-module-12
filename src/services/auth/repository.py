from datetime import datetime
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth.jwt_auth import auth_service
from conf.config import app_config

conf = ConnectionConfig(
    MAIL_USERNAME=app_config.MAIL_USERNAME,
    MAIL_PASSWORD=app_config.MAIL_PASSWORD,
    MAIL_FROM=app_config.MAIL_FROM,
    MAIL_PORT=app_config.MAIL_IMAP_PORT,
    MAIL_SERVER=app_config.MAIL_SERVER,
    MAIL_FROM_NAME=f'Woolyc.com msg system - {datetime.now().strftime("%I:%M %p")}',
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)

async def send_verify_email(email: str, username: str, host: str):
    """
    Sends a verification email to a user.

    :param email: The email address of the recipient.
    :type email: EmailStr
    :param username: The username of the recipient.
    :type username: str
    :param host: The host URL for email links.
    :type host: str

    :raises ConnectionErrors: If any connection error occurs during the email sending process.
    """
    try:
        token_verification = auth_service.create_email_token({'sub': email})
        message = MessageSchema(
            subject='Confirm your email',
            recipients=[email],
            template_body={'host': host, 'username': username, 'token': token_verification},
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name='verify_email.html')
    except ConnectionErrors as err:
        print(err)


async def send_reset_password_email(email: str, username: str, temp_code: str, host: str):
    """
    Sends a password reset email to a user.

    :param email: The email address of the recipient.
    :type email: EmailStr
    :param username: The username of the recipient.
    :type username: str
    :param temp_code: The temporary code for password reset.
    :type temp_code: str
    :param host: The host URL for email links.
    :type host: str

    :raises ConnectionErrors: If any connection error occurs during the email sending process.
    """
    try:
        token_password_reset = auth_service.create_reset_password_token(email)
        message = MessageSchema(
            subject='Password reset',
            recipients=[email],
            template_body={'host': host, 'username': username, 'temp_code': temp_code,
                           'expires_at': app_config.TEMP_CODE_LIFETIME, 'token': token_password_reset},
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name='get_temp_code.html')
    except ConnectionErrors as err:
        print(err)
