from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session, Query
from typing import Optional, List
from sqlalchemy import select
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken, getRedis
from redis.asyncio import Redis
from src.database.sourcebans import getSourcebans, SbServer, AsyncSession
import json

info_api = APIRouter()

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