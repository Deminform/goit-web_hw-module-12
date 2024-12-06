from conf import messages
from tests.seed_contacts import fake_contacts


def test_create_contacts(client, redis_mock, get_access_token):
    for fake_user in fake_contacts:
        response = client.post('api/contacts', headers={'Authorization': f'Bearer {get_access_token}'}, json={
            "first_name": fake_user['first_name'],
            "last_name": fake_user['last_name'],
            "email": fake_user['email'],
            "phone": fake_user['phone'],
            "birthday": fake_user['birthday'],
            "description": fake_user['description'] if 'description' in fake_user else ''
        })
        assert response.status_code == 201, response.text
        data = response.json()
        assert data['first_name'] == fake_user['first_name']
        assert data['last_name'] == fake_user['last_name']
        assert data['email'] == fake_user['email']
        assert data['phone'] == fake_user['phone']
        assert data['birthday'] == fake_user['birthday']
        assert data['description'] == fake_user['description'] if 'description' in fake_user else ''

def test_create_contacts__if_exist(client, redis_mock, get_access_token):
    response = client.post('api/contacts', headers={'Authorization': f'Bearer {get_access_token}'}, json={
        "first_name": "Jason",
        "last_name": "McCoy",
        "email": "jason@example.com",
        "phone": "123654987",
        "birthday": "1997-10-10",
        "description": "Test description"
    })
    assert response.status_code == 409, response.text
    data = response.json()
    assert data['detail'] == messages.CONTACT_ALREADY_EXISTS

def test_get_contacts(client, redis_mock, get_access_token, setup_cache):
    response = client.get('api/contacts', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]['first_name'] == fake_contacts[0]['first_name']
    assert data[0]['last_name'] == fake_contacts[0]['last_name']
    assert data[0]['email'] == fake_contacts[0]['email']
    assert data[0]['phone'] == fake_contacts[0]['phone']
    assert data[0]['birthday'] == fake_contacts[0]['birthday']
    assert data[0]['description'] == fake_contacts[0]['description']
    assert data[7]['first_name'] == fake_contacts[7]['first_name']
    assert data[7]['last_name'] == fake_contacts[7]['last_name']
    assert data[7]['email'] == fake_contacts[7]['email']
    assert data[7]['phone'] == fake_contacts[7]['phone']
    assert data[7]['birthday'] == fake_contacts[7]['birthday']
    assert data[7]['description'] == fake_contacts[7]['description']

def test_get_contacts__by_offset(client, redis_mock, get_access_token, setup_cache):
    response = client.get('api/contacts/?limit=10&offset=14', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 6

def test_get_contacts__by_limit(client, redis_mock, get_access_token, setup_cache):
    response = client.get('api/contacts/?limit=10&limit=11', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 11

def test_get_contacts__by_filter_email(client, redis_mock, get_access_token, setup_cache):
    response = client.get('api/contacts/?limit=10&offset=0&email=jason%40example.com', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1

def test_get_contacts__by_filter_fullname(client, redis_mock, get_access_token, setup_cache):
    response = client.get('api/contacts/?limit=10&offset=0&fullname=Jason', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) >= 1

def test_get_contacts__by_filter_days_to_birthday(client, redis_mock, get_access_token, setup_cache):
    response = client.get('api/contacts/?limit=10&offset=0&days_to_birthday=365', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) >= 1

def test_get_contact__by_id(client, redis_mock, get_access_token, setup_cache):
    response = client.get('api/contacts/1', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['first_name'] == 'Jason'
    assert data['last_name'] == 'McCoy'
    assert data['email'] == 'jason@example.com'
    assert data['phone'] == '123654987'
    assert data['birthday'] == '1997-10-10'
    assert data['description'] == 'Test description'

def test_get_contact__by_incorrect_id(client, redis_mock, get_access_token, setup_cache):
    response = client.get('api/contacts/514', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 404, response.text
    data = response.json()
    assert data['detail'] == messages.CONTACT_NOT_FOUND

def test_update_contacts(client, redis_mock, get_access_token):
    response = client.put('api/contacts/1', headers={'Authorization': f'Bearer {get_access_token}'}, json={
        "first_name": "Marlin",
        "last_name": "McCoy",
        "phone": "999999999",
        "description": "Test Marlin description"
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['first_name'] == 'Marlin'
    assert data['last_name'] == 'McCoy'
    assert data['phone'] == '999999999'
    assert data['description'] == 'Test Marlin description'

def test_update_contacts__incorrect_id(client, redis_mock, get_access_token):
    response = client.put('api/contacts/512', headers={'Authorization': f'Bearer {get_access_token}'}, json={
        "phone": "8888888888",
    })
    assert response.status_code == 409, response.text
    data = response.json()
    assert data['detail'] == messages.CONTACT_NOT_FOUND

def test_delete_contacts__incorrect_id(client, redis_mock, get_access_token):
    response = client.delete('api/contacts/514', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 409, response.text
    data = response.json()
    assert data['detail'] == messages.CONTACT_NOT_FOUND

def test_delete_contacts(client, redis_mock, get_access_token):
    response = client.delete('api/contacts/1', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 204
