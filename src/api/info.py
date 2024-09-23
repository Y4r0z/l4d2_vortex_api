from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session, Query
from typing import Optional, List
from sqlalchemy import select
import datetime
from src.lib import steam_api as SteamAPI
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken, getRedis
from redis.asyncio import Redis
from src.database.sourcebans import getSourcebans, SbServer, AsyncSession
import json
import asyncio
import logging

from celery import Celery
celery_app = Celery('tasks', broker='redis://localhost:6379/0')

info_api = APIRouter()
DONATER_CACHE_TIME = 86400

@info_api.get('/server/all', response_model=list[Schemas.ServerInfo])
async def get_all_servers(redis: Redis = Depends(getRedis), sb: AsyncSession = Depends(getSourcebans)):
    """
    Возвращает список всех серверов SB.\n
    """
    serversQuery = select(SbServer).where(SbServer.enabled == 1)
    servers = [s._tuple()[0] for s in (await sb.execute(serversQuery)).all()]
    result = []
    for server in servers:
        cached = await redis.get(f'server_info:{server.sid}')
        if cached is not None: result.append(json.loads(cached))
    return result

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




async def createPrivilegedList(user: Models.User, result: list, redis: Redis, privIdList: list[int], isMax = True):
    steamId = user.steamId
    privileges = [i for i in user.privileges if i.privilegeId in privIdList]
    if len(privileges) == 0: return
    rkey = f'steam:{steamId}'
    if (steamInfo:=(await redis.get(rkey))) is None:      
        try:
            steamInfo = await SteamAPI.GetPlayerSummaries(steamId)
        except:
            logging.info(f'Не удалось найти игрока')
            return
        await redis.set(rkey, json.dumps(steamInfo), ex=DONATER_CACHE_TIME)
    else:
        steamInfo = json.loads(steamInfo)
    ff = max if isMax else min
    privilegeStatus = ff(privileges, key=lambda x: x.privilegeId)
    privilege = privilegeStatus.privilege
    if privilegeStatus.activeUntil < datetime.datetime.now(): return
    result.append(
        {
        'steamId':  steamId,
        'steamInfo': steamInfo,
        'privilege': {
            'id': privilege.id,
            'accessLevel': privilege.accessLevel,
            'name': privilege.name,
            'description': privilege.description,
        }
        }
    )
def isBoostyDatetime(d: datetime.datetime) -> bool:
    return d.isoformat()[:19] == Models.BoostyPrivilegeUntil.isoformat()[:19]

@info_api.get('/donaters', response_model=list[Schemas.PrivilegedUserInfo])
async def get_donaters(db: Session = Depends(get_db), redis: Redis = Depends(getRedis)):
    """
    Возвращает список донатеров.\n
    """
    rkey = 'info:donaters'  
    if (cached := await redis.get(rkey)) is not None:
        return json.loads(cached)
    donatersQuery = select(Models.User).filter(Models.User.privileges.any())
    donaters = db.execute(donatersQuery).scalars().all() # Чтобы избавиться от Row[Tuple[User]] -> User
    result = [] # type: ignore
    privIds = [6, 7, 8]
    tasks = [createPrivilegedList(d, result, redis, privIds) for d in donaters]
    await asyncio.gather(*tasks)
    result.sort(key=lambda x: x['privilege']['id'], reverse=True)
    await redis.set(rkey, json.dumps(result), ex=DONATER_CACHE_TIME)
    return result
    
@info_api.get('/team', response_model=list[Schemas.PrivilegedUserInfo])
async def get_team(db: Session = Depends(get_db), redis: Redis = Depends(getRedis)):
    """
    Возвращает состав команды администарторов и модераторов.\n
    """
    rkey = 'info:team'
    if (cached := await redis.get(rkey)) is not None:
        return json.loads(cached)
    adminsQuery = select(Models.User).filter(Models.User.privileges.any())
    admins = db.execute(adminsQuery).scalars().all() # Чтобы избавиться от Row[Tuple[User]] -> User
    result = [] # type: ignore
    privIds = [1, 2, 3]
    tasks = [createPrivilegedList(d, result, redis, privIds, False) for d in admins]
    await asyncio.gather(*tasks)
    result.sort(key=lambda x: x['privilege']['id'], reverse=False)
    await redis.set(rkey, json.dumps(result), ex=DONATER_CACHE_TIME)
    return result