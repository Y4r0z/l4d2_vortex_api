import src.lib.steam_api as SteamAPI
from src.services.cache import CacheService
from redis.asyncio import Redis
import json

class SteamService:
    def __init__(self, redis: Redis):
        self.cache = CacheService(redis)
    
    async def get_player_summary(self, steam_id: str):
        return await self.cache.get_or_set(
            f'steam:{steam_id}',
            lambda: SteamAPI.GetPlayerSummaries(steam_id),
            ttl=3600
        )
    
    async def get_multiple_summaries(self, steam_ids: list[str]):
        results = {}
        for steam_id in steam_ids:
            try:
                results[steam_id] = await self.get_player_summary(steam_id)
            except:
                continue
        return results

def steamid64_to_steamid(steamid64: str) -> str:
    steamid64_int = int(steamid64)
    y = steamid64_int % 2
    z = (steamid64_int - 76561197960265728 - y) // 2
    return f"STEAM_1:{y}:{z}"

def steamid_to_steamid64(steamid: str) -> str:
    parts = steamid.split(":")
    if len(parts) != 3 or parts[0] != "STEAM_1":
        raise ValueError("Invalid SteamID format")
    
    y = int(parts[1])
    z = int(parts[2])
    steamid64 = z * 2 + 76561197960265728 + y
    return str(steamid64)