from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session, Query
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_
import datetime
from src.lib import steam_api as SteamAPI
from src.lib.tools_lib import getUser, requireToken, get_db, getOrCreateUser, checkToken, getRedis
from redis.asyncio import Redis
import json
import asyncio
import logging
from typing import Union
from src.services.steam import SteamService

from celery import Celery
celery_app = Celery('tasks', broker='redis://localhost:6379/0')

info_api = APIRouter()
CACHE_TIME = 3600

@info_api.get('/group', response_model=Schemas.GroupInfo)
async def get_group_info(redis: Redis = Depends(getRedis)):
    group_info = await redis.get('group_info')
    if group_info is None:
        celery_app.send_task('src.celery.tasks.parse_group')
        await asyncio.sleep(5)
        group_info = await redis.get('group_info')
        if group_info is None:
            raise HTTPException(status_code=404, detail="Group info not found")
    
    data = json.loads(group_info)
    if 'timestamp' not in data:
        data['timestamp'] = datetime.datetime.now().timestamp()
        await redis.set('group_info', json.dumps(data), ex=3600)
    elif datetime.datetime.now().timestamp() - data['timestamp'] > 1800:
        celery_app.send_task('src.celery.tasks.parse_group')
    
    return data

async def get_privileged_users(
    db: Session, 
    redis: Redis, 
    privilege_ids: list[int], 
    cache_key: str,
    prefer_max_privilege: bool = True
) -> list[Dict[str, Any]]:
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    try:
        current_time = datetime.datetime.now()
        
        users_query = select(Models.User).join(
            Models.PrivilegeStatus, 
            Models.User.id == Models.PrivilegeStatus.userId
        ).filter(
            Models.PrivilegeStatus.privilegeId.in_(privilege_ids),
            Models.PrivilegeStatus.activeUntil > current_time
        ).distinct()
        
        users = db.execute(users_query).scalars().all()
        result = []
        
        steam_service = SteamService(redis)
        
        BATCH_SIZE = 10
        for i in range(0, len(users), BATCH_SIZE):
            batch = users[i:i+BATCH_SIZE]
            steam_ids = [user.steamId for user in batch]
            steam_data = await steam_service.get_multiple_summaries(steam_ids)
            
            for user in batch:
                current_privileges = [
                    p for p in user.privileges 
                    if p.privilegeId in privilege_ids and p.activeUntil > current_time
                ]
                
                if not current_privileges:
                    continue
                    
                compare_func = max if prefer_max_privilege else min
                privilege_status = compare_func(current_privileges, key=lambda x: x.privilegeId)
                privilege = privilege_status.privilege
                
                steam_info = steam_data.get(user.steamId)
                if not steam_info:
                    continue
                
                result.append({
                    'steamId': user.steamId,
                    'steamInfo': steam_info,
                    'privilege': {
                        'id': privilege.id,
                        'accessLevel': privilege.accessLevel,
                        'name': privilege.name,
                        'description': privilege.description,
                    }
                })
        
        compare_key = 'id' if prefer_max_privilege else 'id'
        result.sort(key=lambda x: x['privilege'][compare_key], reverse=prefer_max_privilege)
        
        await redis.set(cache_key, json.dumps(result), ex=CACHE_TIME)
        return result
    except Exception as e:
        logging.error(f"Error in get_privileged_users: {e}")
        return []

@info_api.get('/donaters', response_model=list[Schemas.PrivilegedUserInfo])
async def get_donaters(db: Session = Depends(get_db), redis: Redis = Depends(getRedis)):
    return await get_privileged_users(
        db, redis, 
        privilege_ids=[6, 7, 8],
        cache_key='info:donaters',
        prefer_max_privilege=True
    )

@info_api.get('/team', response_model=list[Schemas.PrivilegedUserInfo])
async def get_team(db: Session = Depends(get_db), redis: Redis = Depends(getRedis)):
    return await get_privileged_users(
        db, redis,
        privilege_ids=[1, 2, 3], 
        cache_key='info:team',
        prefer_max_privilege=False
    )