from celery import Celery
from celery.signals import worker_ready
import src.settings as settings
from sqlalchemy import select
from src.database.sourcebans import getSourcebansSync, SbServer
from src.lib.rcon_api import getRconPlayers
from src.lib.source_query import getServerInfo, getServerPlayers
import datetime
import redis
import json
import xml.etree.ElementTree as ET
import httpx
import time
from src.database.models import SessionLocal
from src.database import models as Models

celery = Celery(__name__)
celery.conf.broker_url = settings.CELERY_BROKER_URL
celery.conf.result_backend = settings.CELERY_RESULT_BACKEND

celery.conf.update(
	task_acks_late=True,
	task_reject_on_worker_lost=True,
	broker_connection_timeout=10,
	result_extended=True,
	redis_max_connections=20
)

redis_pool = redis.ConnectionPool.from_url(
	settings.REDIS_CONNECT_STRING, 
	db=1,
	socket_timeout=5,
	socket_connect_timeout=5
)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
	sender.add_periodic_task(10.0, fetch_server_info.s(), name='fetch_servers')
	sender.add_periodic_task(600.0, parse_group.s(), name='parse_group')
	sender.add_periodic_task(86400.0, update_music_list.s(), name='update_music_list')

@worker_ready.connect
def at_start(sender, **kwargs):
	with sender.app.connection() as conn:
		sender.app.send_task('src.celery.tasks.parse_group', connection=conn)

def process_single_server(server: SbServer):
	"""
	Обработка информации для одного сервера и сохранение только в Redis
	"""
	players = []
	server_id = f"{server.ip}:{server.port}"
	
	try:
		serverInfo = getServerInfo(server, timeout=5)
	except Exception as e:
		return
	
	try:
		a2sPlayers = getServerPlayers(server)
	except Exception as e:
		a2sPlayers = []

	try:
		rcon_players = getRconPlayers(server)
		
		for p in rcon_players:
			try:
				tt = next((p2.duration for p2 in a2sPlayers if p2.name == p.name), 0)
			except Exception as e:
				tt = 0
			
			players.append({
				'id': p.id,
				'ip': p.ip,
				'name': p.name,
				'time': tt,
				'steamId': p.steam64id
			})
	except Exception as e:
		pass

	finalServer = {
		'id': server.sid,
		'name': serverInfo.server_name,
		'map': serverInfo.map_name,
		'playersCount': serverInfo.player_count,
		'maxPlayersCount': serverInfo.max_players,
		'ip': server.ip,
		'port': server.port,
		'ping': serverInfo.ping,
		'time': datetime.datetime.now().isoformat(),
		'keywords': serverInfo.keywords,
		'players': players
	}

	try:
		with redis.Redis(connection_pool=redis_pool) as r:
			r.set(f'server_info:{server.sid}', json.dumps(finalServer), ex=86400)
	except redis.RedisError as e:
		pass

@celery.task(
	bind=True,
	max_retries=3,
	retry_backoff=True,
	soft_time_limit=300,
	time_limit=360,
	name="fetch_server_info"
)
def fetch_server_info(self):
	"""
	Задача получения информации со всех серверов и сохранения в Redis
	"""
	sb = None
	
	try:
		sb = next(getSourcebansSync())
		
		serversQuery = select(SbServer).where(SbServer.enabled == 1)
		servers = [s._tuple()[0] for s in sb.execute(serversQuery).all()]
		
		for server in servers:
			try:
				process_single_server(server)
			except Exception as e:
				continue
		
	except Exception as exc:
		raise self.retry(exc=exc, countdown=60)
	finally:
		if sb is not None:
			sb.close()

@celery.task(
	bind=True,
	max_retries=3,
	retry_backoff=True,
	soft_time_limit=60,
	time_limit=120,
	name="parse_group"
)
def parse_group(self):
	"""
	Задача получения информации о группе Steam и сохранения только в Redis
	"""
	try:
		group_href = 'https://steamcommunity.com/groups/vortexl4d4'
		href = f'{group_href}/memberslistxml/?xml=1'

		response = httpx.get(href, timeout=10.0)
		response.raise_for_status()
		data = response.text

		root = ET.fromstring(data)
		root = root.find('groupDetails')
		
		if root is None:
			error_message = "Failed to find groupDetails in XML"
			raise ValueError(error_message)

		membersCount = int(root.find('memberCount').text)
		membersInGame = int(root.find('membersInGame').text)
		membersOnline = int(root.find('membersOnline').text)
		
		group_data = {
			'membersCount': membersCount,
			'membersInGame': membersInGame,
			'membersOnline': membersOnline
		}
		
		try:
			with redis.Redis(connection_pool=redis_pool) as r:
				r.set('group_info', json.dumps(group_data), ex=3600)
		except redis.RedisError as e:
			raise
		
	except (httpx.HTTPError, ET.ParseError, ValueError, redis.RedisError) as exc:
		raise self.retry(exc=exc, countdown=60)
	except Exception as exc:
		raise

@celery.task(
    bind=True,
    max_retries=3,
    retry_backoff=True,
    soft_time_limit=300,
    time_limit=360,
    name="update_music_list"
)
def update_music_list(self):
    """
    Задача для управления музыкальной библиотекой:
    1. Обновляет никнеймы пользователей в таблице player_music
    2. Удаляет треки пользователей без привилегий Legend, Moderator, Admin или Owner
    """
    with SessionLocal() as db:
        try:
            music_entries = db.query(Models.PlayerMusic).join(Models.User).all()
            
            steam_ids = []
            music_by_steamid = {}
            deleted_tracks_count = 0
            current_time = datetime.datetime.now()
            
            for entry in music_entries:
                has_required_privilege = False
                
                privileges = db.query(Models.PrivilegeStatus).filter(
                    Models.PrivilegeStatus.userId == entry.userId,
                    Models.PrivilegeStatus.activeUntil > current_time,
                    Models.PrivilegeStatus.privilegeId.in_([1, 2, 3, 8])  # owner, admin, moderator, legend
                ).all()
                
                if privileges:
                    has_required_privilege = True
                
                if not has_required_privilege:
                    db.delete(entry)
                    deleted_tracks_count += 1
                    continue
                
                if entry.user.steamId not in steam_ids:
                    steam_ids.append(entry.user.steamId)
                
                if entry.user.steamId not in music_by_steamid:
                    music_by_steamid[entry.user.steamId] = []
                
                music_by_steamid[entry.user.steamId].append(entry)
            
            if deleted_tracks_count > 0:
                db.commit()
                
            if not steam_ids:
                return
            
            steam_id_chunks = [steam_ids[i:i+100] for i in range(0, len(steam_ids), 100)]
            
            for chunk in steam_id_chunks:
                steam_ids_str = ",".join(chunk)
                try:
                    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={settings.STEAM_TOKEN}&steamids={steam_ids_str}"
                    response = httpx.get(url, timeout=10.0)
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'response' in data and 'players' in data['response']:
                        players = data['response']['players']
                        
                        for player in players:
                            steam_id = player.get('steamid')
                            nick = player.get('personaname')
                            
                            if steam_id and nick and steam_id in music_by_steamid:
                                for music_entry in music_by_steamid[steam_id]:
                                    music_entry.nick = nick
                        
                        db.commit()
                    
                except httpx.HTTPError as e:
                    self.retry(exc=e, countdown=60)
                
                time.sleep(1)
            
        except Exception as exc:
            raise self.retry(exc=exc, countdown=60)