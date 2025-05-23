from typing import Dict, List, Optional, Any
import datetime
import json
from redis.asyncio import Redis
import uuid

QUEUE_PREFIX = "server_queue"
QUEUE_TTL = 300  # Выкинет из очереди через секунд

class QueueService:
	def __init__(self, redis: Redis):
		self.redis = redis
	
	async def join_queue(self, client_id: str, preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		user_key = f"{QUEUE_PREFIX}:user:{client_id}"
		
		if await self.redis.exists(user_key):
			return {
				"success": False,
				"error": "already_in_queue",
				"message": "Вы уже находитесь в очереди автоподключения"
			}
		
		queue_length = await self.redis.llen(f"{QUEUE_PREFIX}:queue")
		
		queue_id = str(uuid.uuid4())
		expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=QUEUE_TTL)
		user_data = {
			"clientId": client_id,
			"queueId": queue_id,
			"joinedAt": datetime.datetime.now().isoformat(),
			"preferences": preferences or {},
			"position": queue_length + 1,
			"expiresAt": expiry_time.isoformat()
		}
		
		await self.redis.set(user_key, json.dumps(user_data), ex=QUEUE_TTL)
		await self.redis.rpush(f"{QUEUE_PREFIX}:queue", client_id)
		
		return {
			"success": True,
			"queueId": queue_id,
			"position": user_data["position"],
			"estimatedWaitTime": self._calculate_wait_time(user_data["position"]),
			"expiresAt": expiry_time.isoformat()
		}
	
	async def get_status(self, client_id: str) -> Dict[str, Any]:
		user_key = f"{QUEUE_PREFIX}:user:{client_id}"
		
		if not await self.redis.exists(user_key):
			return {
				"status": "not_found",
				"message": "Вы не находитесь в очереди автоподключения"
			}
		
		user_data_str = await self.redis.get(user_key)
		user_data = json.loads(user_data_str)
		
		expires_at = datetime.datetime.fromisoformat(user_data["expiresAt"])
		if expires_at <= datetime.datetime.now():
			await self.leave_queue(client_id)
			return {
				"status": "expired",
				"message": "Время ожидания истекло. Попробуйте снова."
			}
		
		position = await self._update_position(client_id)
		user_data["position"] = position
		await self.redis.set(user_key, json.dumps(user_data), ex=QUEUE_TTL)
		
		if position == 1:
			server = await self._find_suitable_server(user_data.get("preferences", {}))
			if server:
				await self.leave_queue(client_id)
				return {
					"status": "server_found",
					"server": server,
					"connectString": f"steam://connect/{server['ip']}:{server['port']}"
				}
		
		return {
			"status": "waiting",
			"position": position,
			"estimatedWaitTime": self._calculate_wait_time(position),
			"expiresAt": user_data["expiresAt"]
		}
	
	async def leave_queue(self, client_id: str) -> Dict[str, Any]:
		user_key = f"{QUEUE_PREFIX}:user:{client_id}"
		
		if not await self.redis.exists(user_key):
			return {
				"success": False,
				"error": "not_in_queue",
				"message": "Вы не находитесь в очереди автоподключения"
			}
		
		await self.redis.lrem(f"{QUEUE_PREFIX}:queue", 0, client_id)
		await self.redis.delete(user_key)
		
		return {
			"success": True,
			"message": "Вы успешно покинули очередь автоподключения"
		}
	
	async def get_queue_info(self) -> Dict[str, Any]:
		queue_length = await self.redis.llen(f"{QUEUE_PREFIX}:queue")
		
		servers_key = "servers:all"
		servers_data = await self.redis.get(servers_key)
		available_servers = 0
		total_active_players = 0
		
		if servers_data:
			servers = json.loads(servers_data)
			for server in servers:
				if isinstance(server.get("players"), list):
					players_count = len(server["players"])
				else:
					players_count = server.get("players", 0)
				
				if players_count < server.get("maxPlayers", 0):
					available_servers += 1
				total_active_players += players_count
		
		return {
			"queueLength": queue_length,
			"averageWaitTime": self._calculate_wait_time(queue_length // 2) if queue_length > 0 else 0,
			"availableServers": available_servers,
			"totalActivePlayers": total_active_players
		}
	
	async def _update_position(self, client_id: str) -> int:
		queue = await self.redis.lrange(f"{QUEUE_PREFIX}:queue", 0, -1)
		try:
			position = queue.index(client_id) + 1
			return position
		except ValueError:
			await self.redis.rpush(f"{QUEUE_PREFIX}:queue", client_id)
			return len(queue) + 1
	
	async def _find_suitable_server(self, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		servers_key = "servers:all"
		servers_data = await self.redis.get(servers_key)
		
		if not servers_data:
			return None
		
		servers = json.loads(servers_data)
		excluded_servers = preferences.get("excludeServers", [])
		
		for server in servers:
			if server.get("id") in excluded_servers:
				continue
			
			if isinstance(server.get("players"), list):
				current_players = len(server["players"])
			else:
				current_players = server.get("players", 0)
			
			max_players = server.get("maxPlayers", 0)
			
			if current_players > 0 and current_players < max_players:
				return {
					"id": server.get("id"),
					"name": server.get("name"),
					"ip": server.get("ip"),
					"port": server.get("port"),
					"players": current_players,
					"maxPlayers": max_players
				}
		
		return None
	
	def _calculate_wait_time(self, position: int) -> int:
		return position * 15