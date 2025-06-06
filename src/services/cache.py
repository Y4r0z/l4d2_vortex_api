import json
from redis.asyncio import Redis
from typing import Any, Optional, Callable, TypeVar
from functools import wraps

T = TypeVar('T')

class CacheService:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def get_or_set(self, key: str, factory: Callable, ttl: int = 3600) -> Any:
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        result = await factory()
        await self.redis.set(key, json.dumps(result), ex=ttl)
        return result
    
    async def get_or_set_sync(self, key: str, factory: Callable, ttl: int = 3600) -> Any:
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        result = factory()
        await self.redis.set(key, json.dumps(result), ex=ttl)
        return result

def cached(key_pattern: str, ttl: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from src.lib.tools_lib import getRedis
            redis = getRedis()
            cache = CacheService(redis)
            
            key = key_pattern.format(*args, **kwargs)
            
            if func.__code__.co_flags & 0x0080:
                return await cache.get_or_set(key, lambda: func(*args, **kwargs), ttl)
            else:
                return await cache.get_or_set_sync(key, lambda: func(*args, **kwargs), ttl)
        return wrapper
    return decorator