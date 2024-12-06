def test_get_all_contacts_for_admin(client, redis_mock, get_access_token):
    response = client.get('api/contacts/all?limit=10&user_id=1', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data is not None

def test_get_all_contacts_for_admin__incorrect_user_id(client, redis_mock, get_access_token):
    response = client.get('api/contacts/all?limit=10&user_id=9875', headers={'Authorization': f'Bearer {get_access_token}'})
    assert response.status_code == 404