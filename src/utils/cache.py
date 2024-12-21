from functools import wraps
from redis import Redis
import json
from typing import Any, Optional, Callable
import logging
from src.settings import REDIS_CONNECT_STRING, REDIS_DATABASE

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.redis = Redis.from_url(
            REDIS_CONNECT_STRING,
            db=REDIS_DATABASE,
            decode_responses=True
        )

    def cached(self, expire_time: int = 300):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Создаем уникальный ключ на основе функции и параметров
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                try:
                    # Пытаемся получить данные из кэша
                    cached_data = self.redis.get(cache_key)
                    if cached_data:
                        return json.loads(cached_data)
                    
                    # Если данных нет в кэше, выполняем функцию
                    result = await func(*args, **kwargs)
                    
                    # Сохраняем результат в кэш
                    self.redis.setex(
                        cache_key,
                        expire_time,
                        json.dumps(result)
                    )
                    
                    return result
                except Exception as e:
                    logger.error(f"Ошибка кэширования: {str(e)}")
                    # В случае ошибки Redis, просто выполняем функцию
                    return await func(*args, **kwargs)
            
            return wrapper
        return decorator

    def invalidate(self, pattern: str):
        """Инвалидация кэша по паттерну"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Ошибка при инвалидации кэша: {str(e)}")

cache_manager = CacheManager()
