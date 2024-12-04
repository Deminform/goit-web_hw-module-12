from unittest.mock import Mock, AsyncMock

import pytest
from src.services.auth.jwt_auth import auth_service


def test_get_contacts(client, redis_mock, get_access_token, setup_cache):
    response = client.get('api/contacts', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 0


def test_create_contacts(client, redis_mock, get_access_token, setup_cache):
    response = client.post('api/contacts', headers={'Authorization': f'Bearer {get_access_token}'}, json={
        "first_name": "Jason",
        "last_name": "McCoy",
        "email": "jason@example.com",
        "phone": "123654987",
        "birthday": "1997-10-10",
        "description": "Test description"
    })
    assert response.status_code == 201, response.text
    data = response.json()
    assert data['first_name'] == 'Jason'
    assert data['last_name'] == 'McCoy'
    assert data['email'] == 'jason@example.com'
    assert data['phone'] == '123654987'
    assert data['birthday'] == '1997-10-10'
    assert data['description'] == 'Test description'
