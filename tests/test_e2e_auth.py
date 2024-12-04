from unittest.mock import Mock, AsyncMock

import pytest
from sqlalchemy import select

from conf import messages
from src.users.models import User
from tests.conftest import TestingSessionLocal

user_data = {'username': 'test', 'email': 'test@test.com', 'password': '000000'}


def test_signup(client, monkeypatch):
    mock_send_mail = Mock()
    monkeypatch.setattr('src.services.auth.repository.send_verify_email', mock_send_mail)
    response = client.post('api/auth/signup', json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data['email'] == user_data['email']
    assert data['username'] == user_data['username']
    assert 'password' not in data
    assert 'avatar' in data


def test_signup__if_exist(client, monkeypatch):
    mock_send_mail = Mock()
    monkeypatch.setattr('src.services.auth.repository.send_verify_email', mock_send_mail)
    response = client.post('api/auth/signup', json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data['detail'] == messages.ACCOUNT_EXIST


def test_login__not_confirmed(client, redis_mock):
    response = client.post('api/auth/login', data={'username': user_data['email'], 'password': user_data['password']})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data['detail'] == messages.EMAIL_NOT_CONFIRMED


@pytest.mark.asyncio
async def test_login(client, redis_mock):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data['email']))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post('api/auth/login', data={'username': user_data['email'], 'password': user_data['password']})
    assert response.status_code == 200, response.text
    data = response.json()
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert 'token_type' in data


def test_login__wrong_email(client, redis_mock):
    response = client.post('api/auth/login', data={'username': 'email', 'password': user_data['password']})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data['detail'] == messages.INCORRECT_EMAIL


def test_login__wrong_password(client, redis_mock):
    response = client.post('api/auth/login', data={'username': user_data['email'], 'password': 'password'})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data['detail'] == messages.INCORRECT_PASSWORD


def test_login__validation_error(client, redis_mock):
    response = client.post('api/auth/login', data={'password': user_data['password']})
    assert response.status_code == 422, response.text
    data = response.json()
    assert 'detail' in data
