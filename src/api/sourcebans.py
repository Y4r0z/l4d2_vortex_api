from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken
from src.database.sourcebans import getSourcebans, AsyncSession
from src.lib.rcon_api import banPlayer, BanExistsError
from src.lib.steam_api import GetPlayerSummaries

sb_api = APIRouter()

@sb_api.post('/ban')
async def ban(
    steam_id: str, reason: str, duration: int,
    token: str = Depends(requireToken), 
    sb: AsyncSession = Depends(getSourcebans),
    db: Session = Depends(get_db)
):
    """
    Банит игрока на серверах SB.\n
    @param steam_id: SteamID64
    @param reason: Причина бана
    @param duration: Длительность бана в секундах
    """
    if duration < 60:
        raise HTTPException(status_code=400, detail="Длительность бана должна быть не менее 60 секунд")
    checkToken(db, token)
    try:
        player = await GetPlayerSummaries(steam_id)
    except:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    try:
        await banPlayer(sb, player['steamid'], duration, reason, player['personaname'])
    except BanExistsError:
        raise HTTPException(status_code=409, detail='Player already has a ban')
    return {"message": f"Player {steam_id} banned for {duration} seconds"}
        
    
    