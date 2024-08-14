import json
from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateBalance, getRedis
import src.lib.steam_api as SteamAPI
from fastapi_filter import FilterDepends
from redis.asyncio import Redis
from pydantic import TypeAdapter

profile_api = APIRouter()

BULK_PROFILE_CACHE_TIME = 3600

"""
GET:
steamInfo
rank
perks
privileges
balance
discord
"""
@profile_api.get('/bulk', response_model=Schemas.BulkProfileInfo)
async def get_bulk_profile_info(steam_id: str, cached: bool = True, db: Session = Depends(get_db), redis: Redis = Depends(getRedis)):
    user = getUser(db, steam_id)
    rkey = f'bulk_profile_info:{steam_id}'
    if (result:=(await redis.get(rkey))) is not None and cached:
        return json.loads(result)
    steamInfo = await SteamAPI.GetPlayerSummaries(user.steamId)
    rank = Crud.get_player_rank(db, user)
    perks = Crud.get_perks(db, user.id)
    privileges = Crud.get_privilegeStatuses(db, user.id)
    balance = getOrCreateBalance(db, user)
    discord = Crud.get_discord_steam(db, user)
    discordId = None
    if discord is not None: discordId = discord.discordId
    result = {
        'steamInfo': steamInfo,
        'rank': rank,
        'perks': perks,
        'privileges': [
            {
                'id':i.id, 
                'activeUntil':i.activeUntil.isoformat(), 
                'user':{'id':i.user.id, 'steamId':i.user.steamId},
                'privilege':{'id':i.privilege.id, 'name':i.privilege.name, 'accessLevel':i.privilege.accessLevel, 'description':i.privilege.description}
            }
            for i in privileges
        ],
        'balance': balance.value,
        'discordId': discordId
    }
    await redis.set(rkey, json.dumps(result), ex=BULK_PROFILE_CACHE_TIME)
    return result