from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session, Query
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_
import datetime
from src.lib import steam_api as SteamAPI
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken, getRedis
from redis.asyncio import Redis
import json
import asyncio
import logging
from typing import Union

from celery import Celery
celery_app = Celery('tasks', broker='redis://localhost:6379/0')

info_api = APIRouter()
DONATER_CACHE_TIME = 3600

@info_api.get('/group', response_model=Schemas.GroupInfo)
async def get_group_info(redis: Redis = Depends(getRedis)):
    """
    Возвращает информацию о группе Steam.\n
    """
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

async def process_privileged_user(user: Models.User, redis: Redis, priv_ids: list[int], is_max: bool = True) -> Union[Dict[str, Any], None]:
    try:
        steamId = user.steamId
        current_time = datetime.datetime.now()
        
        privileges = [p for p in user.privileges 
                    if p.privilegeId in priv_ids and p.activeUntil > current_time]
        
        if not privileges:
            return None
            
        compare_func = max if is_max else min
        privilege_status = compare_func(privileges, key=lambda x: x.privilegeId)
        privilege = privilege_status.privilege
        
        rkey = f'steam:{steamId}'
        cached_info = await redis.get(rkey)
        
        if cached_info is None:
            try:
                steam_info = await SteamAPI.GetPlayerSummaries(steamId)
                await redis.set(rkey, json.dumps(steam_info), ex=DONATER_CACHE_TIME)
            except Exception:
                return None
        else:
            steam_info = json.loads(cached_info)
            
        return {
            'steamId': steamId,
            'steamInfo': steam_info,
            'privilege': {
                'id': privilege.id,
                'accessLevel': privilege.accessLevel,
                'name': privilege.name,
                'description': privilege.description,
            }
        }
    except Exception:
        return None

@info_api.get('/donaters', response_model=list[Schemas.PrivilegedUserInfo])
async def get_donaters(db: Session = Depends(get_db), redis: Redis = Depends(getRedis)):
    """
    Возвращает список донатеров.\n
    """
    rkey = 'info:donaters'  
    if (cached := await redis.get(rkey)) is not None:
        return json.loads(cached)
    
    try:
        current_time = datetime.datetime.now()
        priv_ids = [6, 7, 8]  # VIP, Premium, Legend
        
        donaters_query = select(Models.User).join(
            Models.PrivilegeStatus, 
            Models.User.id == Models.PrivilegeStatus.userId
        ).filter(
            Models.PrivilegeStatus.privilegeId.in_(priv_ids),
            Models.PrivilegeStatus.activeUntil > current_time
        ).distinct()
        
        donaters = db.execute(donaters_query).scalars().all()
        result = []
        
        BATCH_SIZE = 10
        for i in range(0, len(donaters), BATCH_SIZE):
            batch = donaters[i:i+BATCH_SIZE]
            tasks = []
            
            for user in batch:
                tasks.append(process_privileged_user(user, redis, priv_ids, True))
                
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for item in batch_results:
                if item is not None and not isinstance(item, Exception):
                    result.append(item)
        
        result.sort(key=lambda x: x['privilege']['id'], reverse=True)
        await redis.set(rkey, json.dumps(result), ex=DONATER_CACHE_TIME)
        return result
    except Exception as e:
        logging.error(f"Error in get_donaters: {e}")
        return []

@info_api.get('/team', response_model=list[Schemas.PrivilegedUserInfo])
async def get_team(db: Session = Depends(get_db), redis: Redis = Depends(getRedis)):
    """
    Возвращает состав команды администарторов и модераторов.\n
    """
    rkey = 'info:team'
    if (cached := await redis.get(rkey)) is not None:
        return json.loads(cached)
    
    try:
        current_time = datetime.datetime.now()
        priv_ids = [1, 2, 3]  # Owner, Admin, Moderator
        
        admins_query = select(Models.User).join(
            Models.PrivilegeStatus, 
            Models.User.id == Models.PrivilegeStatus.userId
        ).filter(
            Models.PrivilegeStatus.privilegeId.in_(priv_ids),
            Models.PrivilegeStatus.activeUntil > current_time
        ).distinct()
        
        admins = db.execute(admins_query).scalars().all()
        result = []
        
        BATCH_SIZE = 10
        for i in range(0, len(admins), BATCH_SIZE):
            batch = admins[i:i+BATCH_SIZE]
            tasks = []
            
            for user in batch:
                tasks.append(process_privileged_user(user, redis, priv_ids, False))
                
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for item in batch_results:
                if item is not None and not isinstance(item, Exception):
                    result.append(item)
        
        result.sort(key=lambda x: x['privilege']['id'])
        await redis.set(rkey, json.dumps(result), ex=DONATER_CACHE_TIME)
        return result
    except Exception as e:
        logging.error(f"Error in get_team: {e}")
        return []