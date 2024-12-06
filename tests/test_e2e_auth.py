from unittest.mock import Mock

import pytest
from sqlalchemy import select

from conf import messages
from src.services.auth.jwt_auth import auth_service
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


def test_verify_email(client, redis_mock):
    email_token = auth_service.create_email_token(data={"sub": user_data['email']})
    response = client.get(f'api/auth/verify_email/{email_token}')
    assert response.status_code == 200, response.text
    data = response.json()
    assert data == {"message": "Email confirmed"}


@pytest.mark.asyncio
async def test_login(client, redis_mock):
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


def test_refresh_token(client, redis_mock):
    response_login = client.post('api/auth/login', data={'username': user_data['email'], 'password': user_data['password']})
    if response_login.status_code == 200:
        data = response_login.json()
        response_refresh_token = client.get('api/auth/refresh_token', headers={'Authorization': f'Bearer {data['refresh_token']}'})
        assert response_refresh_token.status_code == 200, response_refresh_token.text
        data = response_refresh_token.json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'token_type' in data


def test_refresh_token__wrong_token(client, redis_mock):
    response_refresh_token = client.get('api/auth/refresh_token', headers={'Authorization': f'Bearer wrong_token'})
    assert response_refresh_token.status_code == 401, response_refresh_token.text
    data = response_refresh_token.json()
    assert data['detail'] == messages.INCORRECT_REFRESH_TOKEN


