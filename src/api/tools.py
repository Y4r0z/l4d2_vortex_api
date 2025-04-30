from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import InstrumentedAttribute
from src.database.models import SessionLocal
from src.database import crud as Crud, models as Models
from sqlalchemy.orm import Session, Query
from typing import Optional, TypeVar, Any, Generator
import redis.asyncio as aioredis # type: ignore
from src.settings import REDIS_CONNECT_STRING, REDIS_DATABASE
from contextlib import asynccontextmanager

security = HTTPBearer()

def getUser(db: Session, steam_id: str) -> Models.User:
    """
    Получает пользователя по Steam ID с проверкой существования
    """
    try:
        user = Crud.get_user(db, steam_id)
        if not user: 
            raise HTTPException(status_code=404, detail='User not found!')
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error getting user data")

def requireToken(auth: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Проверяет наличие токена авторизации
    """
    if auth is None: 
        raise HTTPException(status_code=401, detail="Bearer token not found!")
    return auth.credentials

def get_db() -> Generator[Session, None, None]:
    """
    Предоставляет сессию базы данных с корректной обработкой ошибок
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

def getOrCreateUser(db: Session, steam_id: str) -> Models.User:
    """
    Получает существующего пользователя или создает нового
    """
    try:
        user = Crud.get_user(db, steam_id)
        if not user:
            user = Crud.create_user(db, steam_id)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to get or create user"
        )

def checkToken(db: Session, token: str) -> None:
    """
    Проверяет валидность токена
    """
    try:
        if not Crud.check_token(db, token): 
            raise HTTPException(status_code=401, detail="Bearer token is not valid!")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Error validating authentication token"
        )

T = TypeVar('T', bound=Models.IDModel)
def findByID(db: Session, model: type[T], id: int) -> T | None:
    """
    Находит объект по ID
    """
    try:
        return db.query(model).filter(model.id == id).first()
    except Exception as e:
        raise

def findByIDOrAbort(db: Session, model: type[T], id: int) -> T:
    """
    Находит объект по ID или вызывает ошибку 404
    """
    try:
        if (obj := findByID(db, model, id)) is None: 
            raise HTTPException(404, f'Object of type <{model.__tablename__}> ({id}) not found')
        return obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving {model.__name__}"
        )

T2 = TypeVar('T2', bound=Models.Base)
def findByField(db: Session, model: type[T2], field: InstrumentedAttribute, value: Any) -> T2 | None:
    """
    Находит объект по значению поля
    """
    try:
        return db.query(model).filter(field == value).first()
    except Exception as e:
        raise

def findByFieldOrAbort(db: Session, model: type[T2], field: InstrumentedAttribute, value: Any) -> T2:
    """
    Находит объект по значению поля или вызывает ошибку 404
    """
    try:
        if (obj := findByField(db, model, field, value)) is None: 
            raise HTTPException(404, f'Object of type <{model.__tablename__}> with {field.key}={value} not found')
        return obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving {model.__name__}"
        )

redis_pool = None

def createRedisPool():
    """
    Создает пул соединений Redis с обработкой ошибок
    """
    try:
        return aioredis.ConnectionPool.from_url(
            REDIS_CONNECT_STRING, 
            encoding='utf-8', 
            decode_responses=True, 
            db=REDIS_DATABASE,
            max_connections=100,
            socket_timeout=5,
            socket_connect_timeout=5
        )
    except Exception as e:
        raise

redis_pool = createRedisPool()

def getRedis():
    """
    Возвращает клиент Redis из пула соединений
    """
    if redis_pool is None:
        raise HTTPException(status_code=500, detail="Redis connection pool not initialized")
    return aioredis.Redis(connection_pool=redis_pool)

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    """
    yield
    try:
        redis = getRedis()
        await redis.save()
        await redis.close()
    except Exception as e:
        print("Не удалось сохранить Redis")

def getOrCreateBalance(db: Session, user: Models.User):
    """
    Получает или создает баланс пользователя с обработкой ошибок
    """
    try:
        if db.query(Models.Balance).filter(Models.Balance.userId == user.id).first() is None:
            balance = Models.Balance(user=user, value=0)
            db.add(balance)
            db.commit()
            db.refresh(user)
        return user.balance
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to get or create user balance"
        )