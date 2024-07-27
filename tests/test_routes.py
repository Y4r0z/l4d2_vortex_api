
import pytest
from dotenv import load_dotenv
import os
import datetime

load_dotenv(override=True)

token = os.environ.get('SERVER_TOKEN')
oldhost = os.environ.get('LOCAL_MYSQL_HOST')
newhost = 'localhost'
uri = os.environ.get('SQL_CONNECT_STRING').replace(oldhost, newhost) # type: ignore
os.environ['SQL_CONNECT_STRING'] = uri



from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
client.headers['Authorization'] = f'Bearer {token}'
perkset = {
    'survivorPerk1': 'str',
    'survivorPerk2': 'str',
    'survivorPerk3': 'str',
    'survivorPerk4': 'str',
    'boomerPerk': 'str',
    'smokerPerk': 'str',
    'hunterPerk': 'str',
    'jockeyPerk': 'str',
    'spitterPerk': 'str',
    'chargerPerk': 'str',
    'tankPerk': 'str'
}


@pytest.fixture(autouse=True)
def run_fixture():
    # setup
    ...
    yield
    # teardown
    ...


def test_perks_post():
    r = client.post(f'/perks?steam_id=test_client', json=perkset)
    assert r.status_code == 200

def test_perks_get():
    r = client.get(f'/perks?steam_id=test_client')
    assert r.status_code == 200

def test_privilege():
    r1 = client.post(f'/privilege?steam_id=test_client&privilege_id=5&until=2030-01-01T00:00:00')
    assert r1.status_code == 200
    r2 = client.get(f'/privilege?steam_id=test_client')
    assert r2.status_code == 200
    r3 = client.get(f'/privilege/all?steam_id=test_client')
    assert r3.status_code == 200
    priv = r1.json()
    r4 = client.delete(f'/privilege?id={priv["id"]}')
    assert r4.status_code == 200

def test_welcome_phrase():
    r = client.post(f'/privilege/welcome_phrase?steam_id=test_client&phrase=test_phrase')
    assert r.status_code == 200

def test_custom_prefix():
    r = client.post(f'/privilege/custom_prefix?steam_id=test_client&prefix=test_prefix')
    assert r.status_code == 200

def test_privilege_types_get():
    r = client.get('/privilege/types')
    assert r.status_code == 200
    assert len(r.json()) > 0

def test_user_search():
    r = client.get('/user/search?query=test_client')
    assert r.status_code == 200
    assert len(r.json()) > 0



def test_balance():
    r1 = client.post(f'/balance/set?steam_id=test_client&value=100')
    assert r1.status_code == 200
    assert r1.json()['balance']['value'] == 100
    r2 = client.post(f'/balance/add?steam_id=test_client&value=50')
    assert r2.status_code == 200
    assert r2.json()['balance']['value'] == 150
    r3 = client.get(f'/balance?steam_id=test_client')
    assert r3.json()['value'] == 150

def test_pay():
    client.post(f'/balance/set?steam_id=test_client&value=100')
    r = client.post(f'/balance/pay?source_steam_id=test_client&target_steam_id=server&value=70')
    assert r.status_code == 200
    assert r.json()['source']['value'] == 30


logs = [{
    'steamId': 'test_client',
    'nickname': 'test_nickname',
    'text': 'testing some stuff',
    'time': datetime.datetime.now().isoformat(),
    'server': 'test',
    'team': 1,
    'chatTeam': 0
}]
def test_logs():
    r1 = client.post('/logs', json=logs)
    assert r1.status_code == 200 or r1.status_code == 201
    r2 = client.get('/logs?steam_id=test_client&limit=1')
    assert r2.status_code == 200
    assert len(r2.json()) > 0

def test_discord():
    r1 = client.post('/discord?discord_id=test_discord&steam_id=test_client')
    assert r1.status_code == 200
    r2 = client.get('/discord?discord_id=test_discord')
    assert r2.status_code == 200
    r3 = client.get('/discord/steam?steam_id=test_client')
    assert r3.status_code == 200
