from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session, Query
from typing import Optional, List
from sqlalchemy import select
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken, getRedis
from redis.asyncio import Redis
import json

DEFAULT_EXPIRE = 86400
PREIFX = 'values_api'

values_api = APIRouter()

@values_api.post('/int', response_model=int)
async def set_int(
    key: str, value: int, expire: int = DEFAULT_EXPIRE,
    redis: Redis = Depends(getRedis),
    db: Session = Depends(get_db),
    token: str = Depends(requireToken)):
    checkToken(db, token)
    rkey = f'{PREIFX}:int:{key}'
    await redis.set(rkey, value, ex=expire)
    return value

@values_api.get('/int', response_model=int)
async def get_int(key: str, redis: Redis = Depends(getRedis)):
    rkey = f'{PREIFX}:int:{key}'
    value = await redis.get(rkey)
    if value is None:
        raise HTTPException(status_code=404, detail="Value not found")
    return int(value)

@values_api.delete('/int')
async def delete_int(key: str, redis: Redis = Depends(getRedis)):
    rkey = f'{PREIFX}:int:{key}'
    await redis.delete(rkey)
    return "deleted"


@values_api.post('/string', response_model=str)
async def set_string(
    key: str, value: str, expire: int = DEFAULT_EXPIRE,
    redis: Redis = Depends(getRedis),
    db: Session = Depends(get_db),
    token: str = Depends(requireToken)):
    checkToken(db, token)
    rkey = f'{PREIFX}:string:{key}'
    await redis.set(rkey, value, ex=expire)
    return value

@values_api.get('/string', response_model=str)
async def get_string(key: str, redis: Redis = Depends(getRedis)):
    rkey = f'{PREIFX}:string:{key}'
    value = await redis.get(rkey)
    if value is None:
        raise HTTPException(status_code=404, detail="Value not found")
    return str(value)

@values_api.delete('/string')
async def delete_string(key: str, redis: Redis = Depends(getRedis)):
    rkey = f'{PREIFX}:string:{key}'
    await redis.delete(rkey)
    return "deleted"