import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env.test'), override=True)
os.environ['TESTING'] = '1'

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_refresh_flow():
    client.post('/users/register', json={'username':'rfuser','email':'rf@example.com','password':'pass123'})
    login = client.post('/users/login', data={'username':'rfuser','password':'pass123'})
    assert login.status_code == 200
    refresh = login.json().get('refresh_token')
    assert refresh
    # API expects body {'token': <refresh_token>} per router implementation
    res = client.post('/users/refresh', json={'token': refresh})
    assert res.status_code == 200
    assert 'access_token' in res.json()
