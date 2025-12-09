import os
from dotenv import load_dotenv
from app.main import app
from fastapi.testclient import TestClient

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env.test'), override=True)
os.environ['TESTING'] = '1'

client = TestClient(app)

# User registration
def test_register_user():
    response = client.post("/users/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"

# User login
def test_login_user():
    client.post("/users/register", json={
        "username": "loginuser",
        "email": "loginuser@example.com",
        "password": "password123"
    })
    response = client.post("/users/login", data={
        "username": "loginuser",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

# Create contact
def test_create_contact():
    client.post("/users/register", json={
        "username": "contactuser",
        "email": "contactuser@example.com",
        "password": "password123"
    })
    login = client.post("/users/login", data={
        "username": "contactuser",
        "password": "password123"
    })
    token = login.json()["access_token"]
    response = client.post("/contacts/", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "1234567890",
        "birthday": "2000-01-01",
        "extra": "Test"
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "John"
    assert data["email"] == "john.doe@example.com"

# Get contacts
def test_get_contacts():
    client.post("/users/register", json={
        "username": "getcontacts",
        "email": "getcontacts@example.com",
        "password": "password123"
    })
    login = client.post("/users/login", data={
        "username": "getcontacts",
        "password": "password123"
    })
    token = login.json()["access_token"]
    client.post("/contacts/", json={
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "phone": "5555555555",
        "birthday": "1990-05-05",
        "extra": "Extra"
    }, headers={"Authorization": f"Bearer {token}"})
    response = client.get("/contacts/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(c["first_name"] == "Jane" for c in data)

def test_update_contact():
    client.post("/users/register", json={
        "username": "updateuser",
        "email": "updateuser@example.com",
        "password": "password123"
    })
    login = client.post("/users/login", data={
        "username": "updateuser",
        "password": "password123"
    })
    token = login.json()["access_token"]
    response = client.post("/contacts/", json={
        "first_name": "Old",
        "last_name": "Name",
        "email": "old.name@example.com",
        "phone": "1111111111",
        "birthday": "1995-01-01",
        "extra": "Old"
    }, headers={"Authorization": f"Bearer {token}"})
    contact_id = response.json()["id"]
    update = client.put(f"/contacts/{contact_id}", json={
        "first_name": "New",
        "last_name": "Name",
        "email": "old.name@example.com",
        "phone": "2222222222",
        "birthday": "1995-01-01",
        "extra": "Updated"
    }, headers={"Authorization": f"Bearer {token}"})
    assert update.status_code == 200
    assert update.json()["first_name"] == "New"
    assert update.json()["phone"] == "2222222222"

def test_delete_contact():
    client.post("/users/register", json={
        "username": "deleteuser",
        "email": "deleteuser@example.com",
        "password": "password123"
    })
    login = client.post("/users/login", data={
        "username": "deleteuser",
        "password": "password123"
    })
    token = login.json()["access_token"]
    response = client.post("/contacts/", json={
        "first_name": "ToDelete",
        "last_name": "User",
        "email": "delete.user@example.com",
        "phone": "3333333333",
        "birthday": "1999-01-01",
        "extra": "Delete"
    }, headers={"Authorization": f"Bearer {token}"})
    contact_id = response.json()["id"]
    delete = client.delete(f"/contacts/{contact_id}", headers={"Authorization": f"Bearer {token}"})
    assert delete.status_code == 200
    assert delete.json() is True
    get_deleted = client.get(f"/contacts/{contact_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_deleted.status_code == 404

def test_search_contacts():
    client.post("/users/register", json={
        "username": "searchuser",
        "email": "searchuser@example.com",
        "password": "password123"
    })
    login = client.post("/users/login", data={
        "username": "searchuser",
        "password": "password123"
    })
    token = login.json()["access_token"]
    client.post("/contacts/", json={
        "first_name": "Search",
        "last_name": "Target",
        "email": "search.target@example.com",
        "phone": "4444444444",
        "birthday": "1998-01-01",
        "extra": "Search"
    }, headers={"Authorization": f"Bearer {token}"})

    response = client.get("/contacts/search", params={"q": "Search"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    results = response.json()
    assert any(c["first_name"] == "Search" for c in results)
    response_none = client.get("/contacts/search?q=NotExist", headers={"Authorization": f"Bearer {token}"})
    assert response_none.status_code == 200
    assert response_none.json() == []
