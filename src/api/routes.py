from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken


api = APIRouter()

@api.get('/perks', response_model=Schemas.PerkSet)
def get_perks(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    perks = Crud.get_perks(db, user.id)
    if not perks: raise HTTPException(status_code=404, detail="This user has no perks!")
    return perks

@api.post('/perks', response_model=Schemas.PerkSet)
def set_perks(steam_id:str, perks: Schemas.PerkSet, token: str = Depends(requireToken), db: Session = Depends(get_db)):
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    perksObj = Crud.set_perks(db, user.id, perks)
    return perksObj

@api.get('/privilege', response_model=Schemas.PrivilegesList)
def get_privileges(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    return Crud.get_privileges(db, user.id)

@api.get('/privilege/all', response_model=List[Schemas.PrivilegeStatus])
def get_privileges_all(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    return Crud.get_privilegeStatuses(db, user.id)

@api.delete('/privilege')
def remove_privilege(id: int, db: Session = Depends(get_db)):
    if not Crud.get_privilegeStatus(db, id): raise HTTPException(status_code=404, detail="Privilege not found!")
    Crud.delete_privilegeStatus(db, id)
    return "removed"

@api.post('/privilege', response_model=Schemas.PrivilegeStatus)
def set_privilege(steam_id: str, privilege_id, until: datetime.datetime, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    priv = Crud.get_privilegeType(db, privilege_id)
    if not priv: raise HTTPException(status_code=404, detail="Privilege not found!")
    return Crud.add_privilege(db, user.id, priv.id, until)

@api.put('/privilege', response_model=Schemas.PrivilegeStatus)
def edit_privilege(id: int, privilege_id, until: datetime.datetime, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    if not Crud.get_privilegeStatus(db, id): raise HTTPException(status_code=404, detail=f"Privilege status with id={id} is NOT FOUND!")
    if not Crud.get_privilegeType(db, privilege_id): raise HTTPException(status_code=404, detail=f"Privilege type with id={privilege_id} is NOT FOUND!")
    return Crud.edit_privilegeStatus(db, id, privilege_id, until)


@api.post('/privilege/welcome_phrase')
def set_welcomePhrase(steam_id: str, phrase:str, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    obj = Crud.set_welcomePhrase(db, user.id, phrase)
    return obj.phrase

@api.post('/privilege/custom_prefix')
def set_customPrefix(steam_id: str, prefix:str, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    obj = Crud.set_customPrefix(db, user.id, prefix)
    return obj.prefix

@api.get('/privilege/types', response_model=List[Schemas.PrivilegeType])
def get_privilegeTypes(db: Session = Depends(get_db)):
    return Crud.get_privilegeTypes(db)

@api.get('/user/search', response_model=List[Schemas.User])
def get_user(query : str, db: Session = Depends(get_db)):
    return Crud.find_users(db, query)

@api.get('/check_token')
def check_token(db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    return "token is valid"
