from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
from src.lib.tools_lib import getUser, requireToken, get_db, getOrCreateUser, checkToken
from src.services.logger import api_logger

discord_api = APIRouter()

@discord_api.get('/search', response_model=List[Schemas.SteamDiscordLink])
def find_discord(query : str, db: Session = Depends(get_db)):
    results = Crud.find_discord(db, query)
    return results

@discord_api.post('', response_model=Schemas.SteamDiscordLink)
def create_link(discord_id: str, steam_id: str, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    """
    Привязывает Discord к Steam, создает нового юзера если не найден
    """
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    link = Crud.create_discord(db, user, discord_id)
    return link

@discord_api.get('', response_model=Schemas.SteamDiscordLink)
def get_discord(discord_id: str, db: Session = Depends(get_db)):
    link = Crud.get_discord(db, discord_id)
    if link is None:
        raise HTTPException(404, f'User, linked to the discord id ({discord_id}) not found!')
    return link

@discord_api.get('/steam', response_model=Schemas.SteamDiscordLink)
def get_discord_by_steam(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    link = Crud.get_discord_steam(db, user)
    if link is None:
        raise HTTPException(404, f'User, linked to the steam id ({steam_id}) not found!')
    return link