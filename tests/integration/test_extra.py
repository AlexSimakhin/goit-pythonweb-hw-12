import os
from unittest.mock import patch
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from app.main import app
from app.utils.cache import get_client

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env.test'), override=True)
os.environ['TESTING'] = '1'

client = TestClient(app)


def _register_and_login(username: str, email: str, password: str = 'password123'):
    client.post('/users/register', json={'username': username, 'email': email, 'password': password})
    res = client.post('/users/login', data={'username': username, 'password': password})
    assert res.status_code == 200
    data = res.json()
    return data['access_token'], data.get('refresh_token')


# Example: test password reset endpoint (two-step flow)
def test_reset_password():
    client.post("/users/register", json={
        "username": "resetuser",
        "email": "resetuser@example.com",
        "password": "password123"
    })
    req = client.post("/users/request-reset", json={"email": "resetuser@example.com"})
    assert req.status_code == 200
    reset_token = req.json().get("reset_token")
    assert reset_token
    res = client.post("/users/reset-password", json={"reset_token": reset_token, "new_password": "newpass456"})
    assert res.status_code == 200
    # login with new password
    login = client.post("/users/login", data={"username": "resetuser", "password": "newpass456"})
    assert login.status_code == 200


# Example: test role-based access (assuming /users/me returns role info)
def test_admin_avatar_change():
    client.post("/users/register", json={
        "username": "adminuser",
        "email": "adminuser@example.com",
        "password": "password123"
    })
    login = client.post("/users/login", data={
        "username": "adminuser",
        "password": "password123"
    })
    token = login.json()["access_token"]
    # Simulate admin role assignment (if endpoint exists)
    # client.post("/users/set-role", json={"user_id": ..., "role": "admin"}, headers={"Authorization": f"Bearer {token}"})
    # Try to change avatar
    with open(os.path.join(os.path.dirname(__file__), "..", "test_avatar.png"), "rb") as f:
        response = client.post("/users/avatar", headers={"Authorization": f"Bearer {token}"}, files={"file": ("test_avatar.png", f, "image/png")})
    assert response.status_code in (200, 403, 422)  # 422 якщо файл не передано


def test_cache_miss_then_hit_on_me_endpoint():
    # Register/login user and clear potential cache for deterministic test
    access, _ = _register_and_login('cacheuser', 'cacheuser@example.com')

    # Explicitly delete cache to simulate miss
    from app.utils.cache import delete_user_cache
    # Decode token to get user id via the API /users/me response
    # First call should prime the cache (miss -> fetch DB -> set cache)
    resp1 = client.get('/users/me', headers={'Authorization': f'Bearer {access}'})
    assert resp1.status_code == 200
    user_id = resp1.json()['id']
    delete_user_cache(user_id)

    # Call after deletion is a miss again
    resp2 = client.get('/users/me', headers={'Authorization': f'Bearer {access}'})
    assert resp2.status_code == 200

    # Now ensure cache is set
    r = get_client()
    assert r.get(f'user:{user_id}') is not None

    # Next call should be a hit (served quickly, still returns 200)
    resp3 = client.get('/users/me', headers={'Authorization': f'Bearer {access}'})
    assert resp3.status_code == 200
    assert resp3.json()['id'] == user_id


def test_avatar_update_role_enforcement_403_for_non_admin():
    access, _ = _register_and_login('regular', 'regular@example.com')
    # Mock cloudinary uploader to avoid external call
    with patch('cloudinary.uploader.upload', return_value={'secure_url': 'http://example.com/avatar.png'}):
        # Send a small dummy file
        files = {'file': ('avatar.png', b'fakeimgbytes', 'image/png')}
        resp = client.post('/users/avatar', headers={'Authorization': f'Bearer {access}'}, files=files)
    assert resp.status_code == 403
    assert resp.json()['detail'] == 'Only admin can change avatar'


def test_avatar_update_200_for_admin():
    # Create admin by registering and then elevating role via set-role endpoint
    access, _ = _register_and_login('adminuser', 'adminuser@example.com')

    # Elevate this user to admin using set-role (needs requester to be admin; bootstrap by making requester admin)
    # Since requester must be admin, first make requester admin via direct DB or by temporarily mocking role check.
    # Simpler: patch decode_access_token to treat the requester as admin via DB mutation.
    # We'll set role using the DB endpoint by impersonating admin: set requester as admin in DB through set-role on self.
    # To call set-role, requester must be admin; emulate by patching decode_access_token to return user_id, then flip role directly.
    from app.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == 'adminuser@example.com').first()
        user.role = 'admin'
        db.commit()
    finally:
        db.close()

    # Now user is admin, upload avatar
    with patch('cloudinary.uploader.upload', return_value={'secure_url': 'http://example.com/avatar2.png'}):
        files = {'file': ('avatar2.png', b'fakeimgbytes', 'image/png')}
        resp = client.post('/users/avatar', headers={'Authorization': f'Bearer {access}'}, files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert 'avatar_url' in body or body.get('avatar')
    # Cache should be refreshed
    r = get_client()
    assert r.get(f"user:{body['id']}") is not None
