from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.database.models import SessionLocal
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional

security = HTTPBearer()

api = FastAPI()

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


@api.get('/perks', response_model=Schemas.PerkSet)
def get_perks(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    perks = Crud.get_perks(db, user.id)
    if not perks: raise HTTPException(status_code=404, detail="This user has no perks!")
    return perks

@api.post('/perks', response_model=Schemas.PerkSet)
def set_perks(steam_id:str, perks: Schemas.PerkSet, token: str = Depends(requireToken), db: Session = Depends(get_db)):
    if not Crud.check_token(db, token): raise HTTPException(status_code=401, detail="Bearer token is not valid!")
    user = getUser(db, steam_id)
    perks = Crud.set_perks(db, user.id, perks)
    return perks
