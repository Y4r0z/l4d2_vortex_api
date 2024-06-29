from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.database.models import SessionLocal
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime


security = HTTPBearer()

api = APIRouter()

def getUser(db : Session, steam_id : str) -> Models.User:
    user = Crud.get_user(db, steam_id)
    if not user: raise HTTPException(status_code=404, detail='User not found!')
    return user

def requireToken(auth : Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    if auth is None: raise HTTPException(status_code=401, detail="Bearer token not found!")
    return auth.credentials


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def getOrCreateUser(db: Session, steam_id:str) -> Models.User:
    user = Crud.get_user(db, steam_id)
    if not user:
        user = Crud.create_user(db, steam_id)
    return user

def checkToken(db:Session, token:str):
    if not Crud.check_token(db, token): raise HTTPException(status_code=401, detail="Bearer token is not valid!")

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
    perks = Crud.set_perks(db, user.id, perks)
    return perks

@api.get('/privilege', response_model=Schemas.PrivilegesList)
def get_privileges(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    return Crud.get_privileges(db, user.id)

@api.post('/privilege', response_model=Schemas.PrivilegeStatus)
def set_privilege(steam_id: str, privilege_id, until: datetime.datetime, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    priv = Crud.get_privilegeType(db, privilege_id)
    if not priv: raise HTTPException(status_code=404, detail="Privilege not found!")
    return Crud.add_privilege(db, user.id, priv.id, until)

@api.post('/privilege/welcome_phrase')
def set_welcomePhrase(steam_id: str, phrase:str, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    obj = Crud.set_welcomePhrase(db, user.id, phrase)
    return obj.phrase

@api.post('/privilege/custom_prefix')
def set_welcomePhrase(steam_id: str, prefix:str, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    obj = Crud.set_customPrefix(db, user.id, prefix)
    return obj.prefix

@api.get('/privilege/types', response_model=List[Schemas.PrivilegeType])
def get_privilegeTypes(db: Session = Depends(get_db)):
    return Crud.get_privilegeTypes(db)