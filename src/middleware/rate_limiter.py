from fastapi import Request, HTTPException
from redis import Redis
import time
from src.settings import REDIS_CONNECT_STRING, REDIS_DATABASE

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.redis = Redis.from_url(
            REDIS_CONNECT_STRING,
            db=REDIS_DATABASE,
            decode_responses=True
        )
        self.requests_per_minute = requests_per_minute

    async def __call__(self, request: Request):
        client_ip = request.client.host
        current = int(time.time())
        key = f"rate_limit:{client_ip}:{current // 60}"
        
        try:
            requests = self.redis.incr(key)
            if requests == 1:
                self.redis.expire(key, 60)
            
            if requests > self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later."
                )
        except Exception as e:
            # В случае проблем с Redis, позволяем запросу пройти
            # но логируем ошибку
            print(f"Rate limiter error: {str(e)}")
