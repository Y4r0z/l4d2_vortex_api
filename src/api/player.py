import json
from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken, getRedis
import src.lib.steam_api as SteamAPI
from redis.asyncio import Redis

player_api = APIRouter()

BULK_PROFILE_CACHE_TIME = 3600

def perkSetToDict(perk_set: Models.PerkSet | None) -> dict:
    if perk_set is None: return None
    return {
        'survivorPerk1': perk_set.survivorPerk1,
        'survivorPerk2': perk_set.survivorPerk2,
        'survivorPerk3': perk_set.survivorPerk3,
        'survivorPerk4': perk_set.survivorPerk4,
        'boomerPerk': perk_set.boomerPerk,
        'smokerPerk': perk_set.smokerPerk,
        'hunterPerk': perk_set.hunterPerk,
        'jockeyPerk': perk_set.jockeyPerk,
        'spitterPerk': perk_set.spitterPerk,
        'chargerPerk': perk_set.chargerPerk,
        'tankPerk': perk_set.tankPerk
    }

@player_api.get('/search', response_model=List[Schemas.User])
def search_players(query: str, db: Session = Depends(get_db)):
    return Crud.find_users(db, query)

@player_api.get('/{steam_id}/profile', response_model=Schemas.BulkProfileInfo)
async def get_player_profile(steam_id: str, cached: bool = True, db: Session = Depends(get_db), redis: Redis = Depends(getRedis)):
    user = getUser(db, steam_id)
    rkey = f'bulk_profile_info:{steam_id}'
    if (result:=(await redis.get(rkey))) is not None and cached:
        return json.loads(result)
    try:   
        steamInfo = await SteamAPI.GetPlayerSummaries(user.steamId)
    except:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    rank = Crud.get_player_rank(db, user)
    perks = Crud.get_perks(db, user.id)
    privileges = Crud.get_privilegeStatuses(db, user.id)
    from src.api.tools import getOrCreateBalance
    balance = getOrCreateBalance(db, user)
    discord = Crud.get_discord_steam(db, user)
    discordId = None
    if discord is not None: discordId = discord.discordId
    result = {
        'steamInfo': steamInfo,
        'rank': rank,
        'perks': perkSetToDict(perks),
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

@player_api.get('/{steam_id}/perks', response_model=Schemas.PerkSet)
def get_player_perks(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    perks = Crud.get_perks(db, user.id)
    if not perks: raise HTTPException(status_code=404, detail="This user has no perks!")
    return perks

@player_api.post('/{steam_id}/perks', response_model=Schemas.PerkSet)
def set_player_perks(steam_id: str, perks: Schemas.PerkSet, token: str = Depends(requireToken), db: Session = Depends(get_db)):
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    perksObj = Crud.set_perks(db, user.id, perks)
    return perksObj

@player_api.get('/{steam_id}/privileges', response_model=Schemas.PrivilegesList)
def get_player_privileges(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    return Crud.get_privileges(db, user.id)

@player_api.get('/{steam_id}/privileges/all', response_model=List[Schemas.PrivilegeStatus])
def get_player_privileges_all(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    return Crud.get_privilegeStatuses(db, user.id)

@player_api.post('/{steam_id}/privileges', response_model=Schemas.PrivilegeStatus)
def set_player_privilege(steam_id: str, privilege_id: int, until: datetime.datetime, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    priv = Crud.get_privilegeType(db, privilege_id)
    if not priv: raise HTTPException(status_code=404, detail="Privilege not found!")
    return Crud.add_privilege(db, user.id, priv.id, until)

@player_api.put('/privileges/{privilege_id}', response_model=Schemas.PrivilegeStatus)
def edit_player_privilege(privilege_id: int, new_privilege_id: int, until: datetime.datetime, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    if not Crud.get_privilegeStatus(db, privilege_id): raise HTTPException(status_code=404, detail=f"Privilege status with id={privilege_id} is NOT FOUND!")
    if not Crud.get_privilegeType(db, new_privilege_id): raise HTTPException(status_code=404, detail=f"Privilege type with id={new_privilege_id} is NOT FOUND!")
    return Crud.edit_privilegeStatus(db, privilege_id, new_privilege_id, until)

@player_api.delete('/privileges/{privilege_id}')
def remove_player_privilege(privilege_id: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    if not Crud.get_privilegeStatus(db, privilege_id): raise HTTPException(status_code=404, detail="Privilege not found!")
    Crud.delete_privilegeStatus(db, privilege_id)
    return "removed"

@player_api.post('/{steam_id}/welcome_phrase')
def set_player_welcome_phrase(steam_id: str, phrase: str, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    obj = Crud.set_welcomePhrase(db, user.id, phrase)
    return obj.phrase

@player_api.post('/{steam_id}/custom_prefix')
def set_player_custom_prefix(steam_id: str, prefix: str, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    obj = Crud.set_customPrefix(db, user.id, prefix)
    return obj.prefix

@player_api.get('/privilege/types', response_model=List[Schemas.PrivilegeType])
def get_privilege_types(db: Session = Depends(get_db)):
    return Crud.get_privilegeTypes(db)