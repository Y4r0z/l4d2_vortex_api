from fastapi import Depends, HTTPException, APIRouter
from src.database import models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import datetime
from src.lib.tools_lib import get_db, requireToken, checkToken, getRedis
from redis.asyncio import Redis
import json

servers_api = APIRouter()

SERVERS_CACHE_TIME = 30
SERVERS_INACTIVE_TIMEOUT = 180

def delete_inactive_servers(db: Session):
	cutoff_time = datetime.datetime.now() - datetime.timedelta(seconds=SERVERS_INACTIVE_TIMEOUT)
	inactive_servers = db.query(Models.ServerStatus).filter(Models.ServerStatus.last_update < cutoff_time).all()
	
	deleted_ids = []
	for server in inactive_servers:
		deleted_ids.append(server.id)
		db.delete(server)
	
	if deleted_ids:
		db.commit()
	
	return deleted_ids

async def get_server_by_ip_port(db: Session, ip: str, port: int) -> Models.ServerStatus:
	server = db.query(Models.ServerStatus).filter(
		Models.ServerStatus.ip == ip,
		Models.ServerStatus.port == port
	).first()
	
	if not server:
		server = Models.ServerStatus(
			ip=ip,
			port=port,
			name=f"Server {ip}:{port}",
			map="unknown",
			mode="default",
			max_slots=8,
			current_players=0,
			last_update=datetime.datetime.now()
		)
		db.add(server)
		db.commit()
		db.refresh(server)
	
	return server

def server_to_schema(server: Models.ServerStatus) -> Dict[str, Any]:
	return {
		"id": server.id,
		"name": server.name,
		"map": server.map,
		"players": server.current_players,
		"maxPlayers": server.max_slots,
		"ip": server.ip,
		"port": server.port,
		"mode": server.mode,
		"players": [
			{
				"userId": player.user_id,
				"name": player.name,
				"ip": player.ip,
				"time": player.connection_time,
				"steamId": player.steam_id
			} for player in server.players
		]
	}

@servers_api.get('', response_model=List[Dict[str, Any]])
async def get_all_servers(redis: Redis = Depends(getRedis), db: Session = Depends(get_db)):
	"""
	Получает информацию о всех серверах
	"""
	deleted_ids = delete_inactive_servers(db)
	
	if deleted_ids:
		await redis.delete("servers:all")
		for server_id in deleted_ids:
			await redis.delete(f"servers:{server_id}")
	
	cache_key = "servers:all"
	cached_data = await redis.get(cache_key)
	
	if cached_data:
		return json.loads(cached_data)
	
	servers = db.query(Models.ServerStatus).all()
	result = [server_to_schema(server) for server in servers]
	
	await redis.set(cache_key, json.dumps(result), ex=SERVERS_CACHE_TIME)
	return result

@servers_api.get('/{server_id}', response_model=Dict[str, Any])
async def get_server(server_id: int, db: Session = Depends(get_db), redis: Redis = Depends(getRedis)):
	"""
	Получает информацию о конкретном сервере
	"""
	cache_key = f"servers:{server_id}"
	cached_data = await redis.get(cache_key)
	
	if cached_data:
		return json.loads(cached_data)
	
	server = db.query(Models.ServerStatus).filter(Models.ServerStatus.id == server_id).first()
	if not server:
		raise HTTPException(status_code=404, detail="Сервер не найден")
	
	cutoff_time = datetime.datetime.now() - datetime.timedelta(seconds=SERVERS_INACTIVE_TIMEOUT)
	if server.last_update < cutoff_time:
		db.delete(server)
		db.commit()
		await redis.delete(cache_key)
		await redis.delete("servers:all")
		raise HTTPException(status_code=404, detail="Сервер не найден")
	
	result = server_to_schema(server)
	await redis.set(cache_key, json.dumps(result), ex=SERVERS_CACHE_TIME)
	return result

@servers_api.post('/update')
async def update_server(
	data: Schemas.ServerUpdateRequest,
	db: Session = Depends(get_db),
	redis: Redis = Depends(getRedis),
	token: str = Depends(requireToken)
):
	"""
	Обновляет информацию о сервере по IP:Port
	"""
	checkToken(db, token)
	
	server = await get_server_by_ip_port(db, data.ip, data.port)
	
	server.name = data.name
	server.map = data.map
	server.mode = data.mode
	server.max_slots = data.max_slots
	server.current_players = len(data.players)
	server.last_update = datetime.datetime.now()
	
	existing_players = {p.steam_id: p for p in server.players}
	updated_player_ids = set()
	
	for player_data in data.players:
		steam_id = player_data.get("steamId")
		if not steam_id:
			continue
			
		updated_player_ids.add(steam_id)
		
		if steam_id in existing_players:
			player = existing_players[steam_id]
			player.user_id = player_data.get("userId", 0)
			player.name = player_data.get("name", "Unknown")
			player.ip = player_data.get("ip", "0.0.0.0")
			player.connection_time = player_data.get("time", 0.0)
			player.last_update = datetime.datetime.now()
		else:
			new_player = Models.ServerPlayer(
				server_id=server.id,
				user_id=player_data.get("userId", 0),
				steam_id=steam_id,
				name=player_data.get("name", "Unknown"),
				ip=player_data.get("ip", "0.0.0.0"),
				connection_time=player_data.get("time", 0.0),
				last_update=datetime.datetime.now()
			)
			db.add(new_player)
	
	to_remove = []
	for player in server.players:
		if player.steam_id not in updated_player_ids:
			to_remove.append(player)
	
	for player in to_remove:
		db.delete(player)
	
	db.commit()
	db.refresh(server)
	
	await redis.delete(f"servers:{server.id}")
	await redis.delete("servers:all")
	
	return {"status": "ok", "server_id": server.id}


@servers_api.post('/queue/join')
async def join_queue(
	data: Schemas.QueueJoinRequest,
	redis: Redis = Depends(getRedis),
	db: Session = Depends(get_db),
	token: str = Depends(requireToken)
):
	"""
	Добавляет пользователя в очередь на автоподключение
	"""
	checkToken(db, token)
	from src.services.queue import QueueService
	queue_service = QueueService(redis)
	return await queue_service.join_queue(data.clientId, data.preferences)

@servers_api.get('/queue/status')
async def check_queue_status(
	client_id: str,
	redis: Redis = Depends(getRedis)
):
	"""
	Проверяет статус пользователя в очереди и возможность подключения
	"""
	from src.services.queue import QueueService
	queue_service = QueueService(redis)
	return await queue_service.get_status(client_id)

@servers_api.delete('/queue/leave')
async def leave_queue(
	data: Schemas.QueueLeaveRequest,
	redis: Redis = Depends(getRedis),
	db: Session = Depends(get_db),
	token: str = Depends(requireToken)
):
	"""
	Удаляет пользователя из очереди (отмена автоподключения)
	"""
	checkToken(db, token)
	from src.services.queue import QueueService
	queue_service = QueueService(redis)
	return await queue_service.leave_queue(data.clientId)

@servers_api.get('/queue/info')
async def get_queue_info(
	redis: Redis = Depends(getRedis)
):
	"""
	Предоставляет общую информацию о текущем состоянии очереди
	"""
	from src.services.queue import QueueService
	queue_service = QueueService(redis)
	return await queue_service.get_queue_info()