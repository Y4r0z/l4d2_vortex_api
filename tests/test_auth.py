import pytest
from dotenv import load_dotenv
import os
import datetime
import jwt

load_dotenv(override=True)

token = os.environ.get('SERVER_TOKEN')
oldhost = os.environ.get('LOCAL_MYSQL_HOST')
newhost = 'localhost'
uri = os.environ.get('SQL_CONNECT_STRING').replace(oldhost, newhost)
os.environ['SQL_CONNECT_STRING'] = uri

from fastapi.testclient import TestClient
from main import app
from src.settings import SECRET_KEY

client = TestClient(app)
client.headers['Authorization'] = f'Bearer {token}'

steam_verify_data = {
    'steamid': '76561198123456789',
    'personaname': 'TestPlayer',
    'avatar': 'https://avatars.steamstatic.com/test_avatar.jpg',
    'avatarfull': 'https://avatars.steamstatic.com/test_avatar_full.jpg',
    'profileurl': 'https://steamcommunity.com/profiles/76561198123456789'
}

@pytest.fixture(autouse=True)
def run_fixture():
    yield

def get_auth_token():
    """Вспомогательная функция для получения JWT токена"""
    response = client.post('/auth/steam/verify', json=steam_verify_data)
    assert response.status_code == 200
    data = response.json()
    return data['access_token']

def test_steam_verify():
    response = client.post('/auth/steam/verify', json=steam_verify_data)
    assert response.status_code == 200
    
    data = response.json()
    assert 'access_token' in data
    assert 'user' in data
    assert 'steamInfo' in data
    assert 'privileges' in data
    
    user_data = data['user']
    assert 'id' in user_data
    assert 'steamId' in user_data
    assert user_data['steamId'].startswith('STEAM_1:')
    
    token = data['access_token']
    decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    assert decoded['sub'] == user_data['id']
    assert decoded['steam_id'] == user_data['steamId']

def test_auth_me():
    token = get_auth_token()
    
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/auth/me', headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert 'user' in data
    assert 'steamInfo' in data  
    assert 'privileges' in data
    
    user_data = data['user']
    assert 'id' in user_data
    assert 'steamId' in user_data
    assert user_data['steamId'].startswith('STEAM_1:')

def test_auth_me_invalid_token():
    headers = {'Authorization': 'Bearer invalid_token'}
    response = client.get('/auth/me', headers=headers)
    assert response.status_code == 401

def test_auth_me_no_token():
    response = client.get('/auth/me')
    assert response.status_code == 401

def test_auth_me_expired_token():
    from src.api.auth import JWT_ALGORITHM
    
    expired_payload = {
        'sub': 999,
        'steam_id': 'STEAM_1:0:999',
        'exp': datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1),
        'iat': datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
    }
    
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    headers = {'Authorization': f'Bearer {expired_token}'}
    response = client.get('/auth/me', headers=headers)
    assert response.status_code == 401

def test_steam_verify_missing_fields():
    incomplete_data = {
        'steamid': '76561198123456789',
        'personaname': 'TestPlayer'
    }
    
    response = client.post('/auth/steam/verify', json=incomplete_data)
    assert response.status_code == 422

def test_steam_verify_invalid_steamid():
    invalid_data = steam_verify_data.copy()
    invalid_data['steamid'] = 'invalid_steamid'
    
    response = client.post('/auth/steam/verify', json=invalid_data)
    assert response.status_code == 500

def test_steamid_conversion():
    from src.api.auth import steamid64_to_steamid, steamid_to_steamid64
    
    steamid64 = '76561198123456789'
    steamid = steamid64_to_steamid(steamid64)
    assert steamid.startswith('STEAM_1:')
    
    converted_back = steamid_to_steamid64(steamid)
    assert converted_back == steamid64

def test_jwt_token_creation():
    from src.api.auth import create_jwt_token
    from src.database.models import User
    
    user = User(id=123, steamId='76561198123456789')
    token = create_jwt_token(user)
    
    decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    assert decoded['sub'] == 123
    assert decoded['steam_id'].startswith('STEAM_1:')
    assert 'exp' in decoded
    assert 'iat' in decoded