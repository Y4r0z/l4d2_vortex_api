from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from src.lib.tools_lib import requireToken, get_db, getOrCreateUser, checkToken, getUser

statistics_api = APIRouter()

@statistics_api.post('/base', response_model=Schemas.StPlayerBase.Output)
def replace_player_base(steam_id: str, base_data: Schemas.StPlayerBase.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
	checkToken(db, token)
	user = getOrCreateUser(db, steam_id)
	return Crud.replace_player_base(db, user.id, base_data)

@statistics_api.get('/base', response_model=Schemas.StPlayerBase.Output)
def get_player_base(steam_id: str, db: Session = Depends(get_db)):
	user = getUser(db, steam_id)
	player_base = Crud.get_player_base(db, user.id)
	if not player_base:
		raise HTTPException(status_code=404, detail="Player base data not found")
	return player_base

@statistics_api.post('/hits', response_model=Schemas.StPlayerHits.Output)
def add_player_hits(steam_id: str, hits_data: Schemas.StPlayerHits.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
	checkToken(db, token)
	user = getOrCreateUser(db, steam_id)
	return Crud.add_player_hits(db, user.id, hits_data)

@statistics_api.get('/hits', response_model=Schemas.StPlayerHits.Output)
def get_player_hits(steam_id: str, db: Session = Depends(get_db)):
	user = getUser(db, steam_id)
	player_hits = Crud.get_player_hits(db, user.id)
	if not player_hits:
		raise HTTPException(status_code=404, detail="Player hits data not found")
	return player_hits

@statistics_api.post('/kills', response_model=Schemas.StPlayerKills.Output)
def add_player_kills(steam_id: str, kills_data: Schemas.StPlayerKills.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
	checkToken(db, token)
	user = getOrCreateUser(db, steam_id)
	return Crud.add_player_kills(db, user.id, kills_data)

@statistics_api.get('/kills', response_model=Schemas.StPlayerKills.Output)
def get_player_kills(steam_id: str, db: Session = Depends(get_db)):
	user = getUser(db, steam_id)
	player_kills = Crud.get_player_kills(db, user.id)
	if not player_kills:
		raise HTTPException(status_code=404, detail="Player kills data not found")
	return player_kills

@statistics_api.post('/shots', response_model=Schemas.StPlayerShots.Output)
def add_player_shots(steam_id: str, shots_data: Schemas.StPlayerShots.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
	checkToken(db, token)
	user = getOrCreateUser(db, steam_id)
	return Crud.add_player_shots(db, user.id, shots_data)

@statistics_api.get('/shots', response_model=Schemas.StPlayerShots.Output)
def get_player_shots(steam_id: str, db: Session = Depends(get_db)):
	user = getUser(db, steam_id)
	player_shots = Crud.get_player_shots(db, user.id)
	if not player_shots:
		raise HTTPException(status_code=404, detail="Player shots data not found")
	return player_shots

@statistics_api.post('/weapon', response_model=Schemas.StPlayerWeapon.Output)
def add_player_weapon(steam_id: str, weapon_data: Schemas.StPlayerWeapon.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
	checkToken(db, token)
	user = getOrCreateUser(db, steam_id)
	return Crud.add_player_weapon(db, user.id, weapon_data)

@statistics_api.get('/weapon', response_model=Schemas.StPlayerWeapon.Output)
def get_player_weapon(steam_id: str, db: Session = Depends(get_db)):
	user = getUser(db, steam_id)
	player_weapon = Crud.get_player_weapon(db, user.id)
	if not player_weapon:
		raise HTTPException(status_code=404, detail="Player weapon data not found")
	return player_weapon