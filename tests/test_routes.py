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
    r = client.post(f'/player/test_client/perks', json=perkset)
    assert r.status_code == 200

def test_perks_get():
    r = client.get(f'/player/test_client/perks')
    assert r.status_code == 200

def test_privilege():
    r1 = client.post(f'/player/test_client/privileges?privilege_id=5&until=2030-01-01T00:00:00')
    assert r1.status_code == 200
    r2 = client.get(f'/player/test_client/privileges')
    assert r2.status_code == 200
    r3 = client.get(f'/player/test_client/privileges/all')
    assert r3.status_code == 200
    priv = r1.json()
    r4 = client.delete(f'/player/privileges/{priv["id"]}')
    assert r4.status_code == 200

def test_welcome_phrase():
    r = client.post(f'/player/test_client/welcome_phrase?phrase=test_phrase')
    assert r.status_code == 200

def test_custom_prefix():
    r = client.post(f'/player/test_client/custom_prefix?prefix=test_prefix')
    assert r.status_code == 200

def test_privilege_types_get():
    r = client.get('/player/privilege/types')
    assert r.status_code == 200
    assert len(r.json()) > 0

def test_user_search():
    r = client.get('/player/search?query=test_client')
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

roundScore = {
    'agression': 11,
    'support': 22,
    'perks': 33,
    'team': 1,
    'time': datetime.datetime.now().replace(microsecond=0).isoformat(),
}
def test_round_score():
    r1 = client.post('/score/round?steam_id=test_client', json=roundScore)
    assert r1.status_code == 200
    score_id = r1.json()['id']
    r2 = client.get(f'/score/round?score_id={score_id}')
    assert r2.status_code == 200
    r2j = r2.json()
    assert r2.json()['id'] == score_id and r2j['agression'] == roundScore['agression'] \
        and r2j['support'] == roundScore['support'] and r2j['perks'] == roundScore['perks'] and r2j['team'] == roundScore['team']
    r3 = client.get(f"/score/round/search?steam_id=test_client&search={roundScore['time'].replace('T', ' ')}")
    assert r3.status_code == 200
    assert len(r3.json()) > 0
    r3j = r3.json()[0]
    assert r3j['time'] == roundScore['time']


playSession = {
    'timeFrom': datetime.datetime.now().replace(microsecond=0).isoformat(),
}
def test_play_session():
    r1 = client.post('/score/session?steam_id=test_client', json=playSession)
    assert r1.status_code == 200
    sid = r1.json()['id']
    r2 = client.get(f'/score/session?session_id={sid}')
    assert r2.status_code == 200
    assert r2.json()['timeFrom'][:16] == playSession['timeFrom'][:16] # секунды округляются на сервере

"""
def test_season():
    r1 = client.post('/score/season/reset')
    assert r1.status_code == 200
    cnt = 4
    for _ in range(cnt):
        ri = client.post('/score/round?steam_id=test_client', json={'agression':10, 'support':20, 'perks': 30})
        assert ri.status_code == 200
    client.post('/score/season/reset')
    r2 = client.get('/score/season/search?steam_id=test_client&order_by=-id')
    assert r2.status_code == 200
    assert len(r2.json()) > 0
    r2j = r2.json()[0]
    sid, a, s, p = r2j['user']['steamId'], r2j['agression'], r2j['support'], r2j['perks']
    assert sid == 'test_client' and a == 10*4 and s == 20*4 and p == 30*4
"""

def test_drop():
    r = client.get('/balance/drop?steam_id=test_client')
    assert r.status_code == 200


giveaway = {
    'activeUntil': (datetime.datetime.now() + datetime.timedelta(days=1)).replace(microsecond=0).isoformat(),
    'useCount': 1,
    'reward': 20
}

def test_giveaway():
    client.post(f'/balance/set?steam_id=test_client2&value=0')
    r1 = client.post(f'/balance/set?steam_id=test_client&value=100')
    assert r1.status_code == 200
    r2 = client.post(f'/balance/giveaway?steam_id=test_client', json=giveaway)
    assert r2.status_code == 200
    r2j = r2.json()
    assert r2j['reward'] == giveaway['reward'] and r2j['maxUseCount'] == giveaway['useCount']
    r3 = client.get(f'/balance/giveaway/checkout?steam_id=test_client2&giveaway_id={r2j["id"]}')
    assert r3.status_code == 200
    r3j = r3.json()
    assert r3j['status'] == 0 and r3j['curUseCount'] == 1
    r4 = client.get(f'/balance/giveaway/checkout?steam_id=test_client2&giveaway_id={r2j["id"]}')
    assert r4.status_code == 400
    r4j = r4.json()
    assert r4j['status'] == 3
    r5 = client.delete(f'/balance/giveaway?giveaway_id={r2j["id"]}')
    assert r5.status_code == 200
    r6 = client.get(f'/balance?steam_id=test_client2')
    assert r6.json()['value'] == 20




l4d2_item = {
    'name': 'Test Item',
    'command': 'give weapon_knife'
}
privilege_item = {
    'name': 'Test Privilege',
    'duration': 3600,
    'privilegeTypeId': 1
}

def test_l4d2_item():
    # Test creating a new L4D2 item
    response = client.post('items/l4d2_item', json=l4d2_item)
    assert response.status_code == 200
    item = response.json()
    assert item['name'] == l4d2_item['name']
    assert item['command'] == l4d2_item['command']

    # Test getting an L4D2 item by id
    item_id = item['id']
    response = client.get(f'items/l4d2_item?item_id={item_id}')
    assert response.status_code == 200
    assert response.json()['id'] == item_id

    # Test getting an L4D2 item by name
    item_name = item['name']
    response = client.get(f'items/l4d2_item/by_name?item_name={item_name}')
    assert response.status_code == 200
    assert response.json()['name'] == item_name

    # Test updating an L4D2 item
    new_item = {'name': 'Updated Test Item', 'command': 'give weapon_deagle'}
    response = client.put(f'items/l4d2_item?item_id={item_id}', json=new_item)
    assert response.status_code == 200
    updated_item = response.json()
    assert updated_item['name'] == new_item['name']
    assert updated_item['command'] == new_item['command']
    
    # Test deleting an L4D2 item
    response = client.delete(f'items/l4d2_item?item_id={item_id}')
    assert response.status_code == 200

# Test the /privilege_item endpoint
def test_privilege_item():
    # Test creating a new privilege item
    response = client.post('items/privilege_item', json=privilege_item)
    assert response.status_code == 200
    item = response.json()
    assert item['name'] == privilege_item['name']
    assert item['duration'] == privilege_item['duration']
    assert item['privilegeType']['id'] == privilege_item['privilegeTypeId']

    # Test getting a privilege item by id
    item_id = item['id']
    response = client.get(f'items/privilege_item?item_id={item_id}')
    assert response.status_code == 200
    assert response.json()['id'] == item_id

    # Test getting a privilege item by name
    item_name = item['name']
    response = client.get(f'items/privilege_item/by_name?item_name={item_name}')
    assert response.status_code == 200
    assert response.json()['name'] == item_name

    # Test updating a privilege item
    new_item = {'name': 'Updated Test Privilege', 'duration': 7200, 'privilegeTypeId': 2}
    response = client.put(f'items/privilege_item?item_id={item_id}', json=new_item)
    assert response.status_code == 200
    updated_item = response.json()
    assert updated_item['name'] == new_item['name']
    assert updated_item['duration'] == new_item['duration']
    assert updated_item['privilegeType']['id'] == new_item['privilegeTypeId']
    
    # Test deleting a privilege item
    response = client.delete(f'items/privilege_item?item_id={item_id}')
    assert response.status_code == 200

from src.database.models import SessionLocal
from src.database import models as Models

def cleanup_statistics_data(steam_id: str):
    with SessionLocal() as db:
        user = db.query(Models.User).filter(Models.User.steamId == steam_id).first()
        if user:
            db.query(Models.StPlayerBase).filter(Models.StPlayerBase.userId == user.id).delete()
            db.query(Models.StPlayerHits).filter(Models.StPlayerHits.userId == user.id).delete()
            db.query(Models.StPlayerKills).filter(Models.StPlayerKills.userId == user.id).delete()
            db.query(Models.StPlayerShots).filter(Models.StPlayerShots.userId == user.id).delete()
            db.query(Models.StPlayerWeapon).filter(Models.StPlayerWeapon.userId == user.id).delete()
            db.commit()

st_player_base_data = {
    'last_nickname': 'TestPlayer',
    'last_online': '2024-01-15',
    'last_ip': '192.168.1.100',
    'last_country': 'Russia',
    'last_city': 'Moscow',
    'last_region': 'Moscow Region'
}

st_player_hits_data = {
    'NULL_HITBOX': 5,
    'HEAD': 150,
    'CHEST': 200,
    'STOMACH': 80,
    'LEFT_ARM': 45,
    'RIGHT_ARM': 50,
    'LEFT_LEG': 30,
    'RIGHT_LEG': 35
}

st_player_kills_data = {
    'survivor_killed': 25,
    'infected_killed': 500,
    'smoker_killed': 35,
    'boomer_killed': 45,
    'hunter_killed': 78,
    'spitter_killed': 28,
    'jockey_killed': 41,
    'charger_killed': 32,
    'witch_killed': 8,
    'tank_killed': 12
}

st_player_shots_data = {
    'player_death': 25,
    'player_fire': 1500,
    'player_hits': 1200,
    'player_heads': 300,
    'player_damage': 50000,
    'player_hurt': 200
}

st_player_weapon_data = {
    'pistol': 100,
    'pistol_magnum': 50,
    'autoshotgun': 200,
    'shotgun_chrome': 150,
    'pumpshotgun': 180,
    'shotgun_spas': 120,
    'smg': 300,
    'smg_mp5': 250,
    'smg_silenced': 220,
    'rifle_ak47': 400,
    'rifle_sg552': 350,
    'rifle': 380,
    'rifle_m60': 80,
    'rifle_desert': 320,
    'hunting_rifle': 150,
    'sniper_military': 100,
    'sniper_awp': 75,
    'sniper_scout': 90,
    'weapon_grenade_launcher': 25,
    'molotov': 45,
    'pipe_bomb': 60,
    'vomitjar': 30,
    'melee': 200,
    'baseball_bat': 50,
    'cricket_bat': 40,
    'crowbar': 60,
    'electric_guitar': 35,
    'fireaxe': 70,
    'frying_pan': 45,
    'katana': 80,
    'knife': 120,
    'machete': 90,
    'tonfa': 55,
    'pain_pills': 150,
    'adrenaline': 80,
    'defibrillator': 25,
    'first_aid_kit': 100
}

def test_statistics_base():
    cleanup_statistics_data('test_client_stats')
    r1 = client.post('/statistics/base?steam_id=test_client_stats', json=st_player_base_data)
    assert r1.status_code == 200
    r1j = r1.json()
    assert r1j['last_nickname'] == st_player_base_data['last_nickname']
    assert r1j['last_country'] == st_player_base_data['last_country']
    
    updated_data = st_player_base_data.copy()
    updated_data['last_nickname'] = 'UpdatedPlayer'
    updated_data['last_city'] = 'Saint Petersburg'
    
    r2 = client.post('/statistics/base?steam_id=test_client_stats', json=updated_data)
    assert r2.status_code == 200
    r2j = r2.json()
    assert r2j['last_nickname'] == 'UpdatedPlayer'
    assert r2j['last_city'] == 'Saint Petersburg'
    
    r3 = client.get('/statistics/base?steam_id=test_client_stats')
    assert r3.status_code == 200
    r3j = r3.json()
    assert r3j['last_nickname'] == 'UpdatedPlayer'
    assert r3j['last_city'] == 'Saint Petersburg'

def test_statistics_hits():
    cleanup_statistics_data('test_client_stats')
    r1 = client.post('/statistics/hits?steam_id=test_client_stats', json=st_player_hits_data)
    assert r1.status_code == 200
    r1j = r1.json()
    assert r1j['HEAD'] == st_player_hits_data['HEAD']
    assert r1j['CHEST'] == st_player_hits_data['CHEST']
    
    add_data = {'HEAD': 50, 'CHEST': 30}
    r2 = client.post('/statistics/hits?steam_id=test_client_stats', json=add_data)
    assert r2.status_code == 200
    r2j = r2.json()
    assert r2j['HEAD'] == st_player_hits_data['HEAD'] + add_data['HEAD']
    assert r2j['CHEST'] == st_player_hits_data['CHEST'] + add_data['CHEST']
    
    r3 = client.get('/statistics/hits?steam_id=test_client_stats')
    assert r3.status_code == 200
    r3j = r3.json()
    assert r3j['HEAD'] == 200
    assert r3j['CHEST'] == 230

def test_statistics_kills():
    cleanup_statistics_data('test_client_stats')
    r1 = client.post('/statistics/kills?steam_id=test_client_stats', json=st_player_kills_data)
    assert r1.status_code == 200
    r1j = r1.json()
    assert r1j['infected_killed'] == st_player_kills_data['infected_killed']
    assert r1j['smoker_killed'] == st_player_kills_data['smoker_killed']
    
    add_data = {'infected_killed': 100, 'smoker_killed': 5}
    r2 = client.post('/statistics/kills?steam_id=test_client_stats', json=add_data)
    assert r2.status_code == 200
    r2j = r2.json()
    assert r2j['infected_killed'] == st_player_kills_data['infected_killed'] + add_data['infected_killed']
    assert r2j['smoker_killed'] == st_player_kills_data['smoker_killed'] + add_data['smoker_killed']
    
    r3 = client.get('/statistics/kills?steam_id=test_client_stats')
    assert r3.status_code == 200
    r3j = r3.json()
    assert r3j['infected_killed'] == 600
    assert r3j['smoker_killed'] == 40

def test_statistics_shots():
    cleanup_statistics_data('test_client_stats')
    r1 = client.post('/statistics/shots?steam_id=test_client_stats', json=st_player_shots_data)
    assert r1.status_code == 200
    r1j = r1.json()
    assert r1j['player_death'] == st_player_shots_data['player_death']
    assert r1j['player_fire'] == st_player_shots_data['player_fire']
    assert r1j['player_hits'] == st_player_shots_data['player_hits']
    
    add_data = {'player_death': 5, 'player_fire': 500, 'player_hits': 400}
    r2 = client.post('/statistics/shots?steam_id=test_client_stats', json=add_data)
    assert r2.status_code == 200
    r2j = r2.json()
    assert r2j['player_death'] == st_player_shots_data['player_death'] + add_data['player_death']
    assert r2j['player_fire'] == st_player_shots_data['player_fire'] + add_data['player_fire']
    assert r2j['player_hits'] == st_player_shots_data['player_hits'] + add_data['player_hits']
    
    r3 = client.get('/statistics/shots?steam_id=test_client_stats')
    assert r3.status_code == 200
    r3j = r3.json()
    assert r3j['player_death'] == 30
    assert r3j['player_fire'] == 2000
    assert r3j['player_hits'] == 1600

def test_statistics_weapon():
    cleanup_statistics_data('test_client_stats')
    r1 = client.post('/statistics/weapon?steam_id=test_client_stats', json=st_player_weapon_data)
    assert r1.status_code == 200
    r1j = r1.json()
    assert r1j['rifle_ak47'] == st_player_weapon_data['rifle_ak47']
    assert r1j['pistol'] == st_player_weapon_data['pistol']
    assert r1j['katana'] == st_player_weapon_data['katana']
    
    add_data = {'rifle_ak47': 100, 'pistol': 50, 'katana': 20}
    r2 = client.post('/statistics/weapon?steam_id=test_client_stats', json=add_data)
    assert r2.status_code == 200
    r2j = r2.json()
    assert r2j['rifle_ak47'] == st_player_weapon_data['rifle_ak47'] + add_data['rifle_ak47']
    assert r2j['pistol'] == st_player_weapon_data['pistol'] + add_data['pistol']
    assert r2j['katana'] == st_player_weapon_data['katana'] + add_data['katana']
    
    r3 = client.get('/statistics/weapon?steam_id=test_client_stats')
    assert r3.status_code == 200
    r3j = r3.json()
    assert r3j['rifle_ak47'] == 500
    assert r3j['pistol'] == 150
    assert r3j['katana'] == 100

def test_statistics_not_found():
    r1 = client.get('/statistics/base?steam_id=non_existent_user')
    assert r1.status_code == 404
    
    r2 = client.get('/statistics/hits?steam_id=non_existent_user')
    assert r2.status_code == 404
    
    r3 = client.get('/statistics/kills?steam_id=non_existent_user')
    assert r3.status_code == 404
    
    r4 = client.get('/statistics/shots?steam_id=non_existent_user')
    assert r4.status_code == 404
    
    r5 = client.get('/statistics/weapon?steam_id=non_existent_user')
    assert r5.status_code == 404