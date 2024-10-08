from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import InstrumentedAttribute
from src.database.models import SessionLocal
from src.database import crud as Crud, models as Models
from sqlalchemy.orm import Session, Query
from typing import Optional, TypeVar, Any
import redis.asyncio as aioredis # type: ignore
from src.settings import REDIS_CONNECT_STRING, REDIS_DATABASE
from contextlib import asynccontextmanager

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

T= TypeVar('T', bound=Models.IDModel)
def findByID(db:Session, model: type[T], id: int) -> T | None:
    return db.query(model).filter(model.id == id).first()

def findByIDOrAbort(db: Session, model: type[T], id: int) -> T:
    if (obj:=findByID(db, model, id)) is None: raise HTTPException(404, f'Object of type <{model.__tablename__}> ({id}) not found')
    return obj

T2 = TypeVar('T2', bound=Models.Base)
def findByField(db:Session, model: type[T2], field: InstrumentedAttribute, value: str) -> T2 | None:
    return db.query(model).filter(field == value).first()

def findByFieldOrAbort(db: Session, model: type[T2], field: InstrumentedAttribute, value: Any) -> T2:
    if (obj:=findByField(db, model, field, value)) is None: raise HTTPException(404, f'Object of type <{model.__tablename__}> with {field.key}={value} not found')
    return obj



def createRedisPool():
    return aioredis.ConnectionPool.from_url(REDIS_CONNECT_STRING, encoding='utf-8', decode_responses=True, db=REDIS_DATABASE)
redis_pool = createRedisPool()
def getRedis():
    return aioredis.Redis(connection_pool=redis_pool)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    ...
    yield
    try:
        await getRedis().save()
    except:
        print ("Не удалось сохранить Redis")
    
# async def getAsyncDB():
#     async with Models.AsyncSessionLocal() as session:
#         yield session


def getOrCreateBalance(db: Session, user: Models.User):
    if db.query(Models.Balance).filter(Models.Balance.userId == user.id).first() is None:
        db.add(Models.Balance(user=user, value=0))
    db.commit()
    db.refresh(user)
    return user.balance