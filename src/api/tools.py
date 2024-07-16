from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.database.models import SessionLocal
from src.database import crud as Crud, models as Models
from sqlalchemy.orm import Session, Query
from typing import Optional, TypeVar


security = HTTPBearer()

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
