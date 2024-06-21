from fastapi import FastAPI, Depends, HTTPException
from src.database.models import SessionLocal
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session


def getUser(db : Session, steam_id : str) -> Models.User:
    user = Crud.get_user(db, steam_id)
    if not user: raise HTTPException(status_code=404, detail='User not found!')
    return user


api = FastAPI()


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

