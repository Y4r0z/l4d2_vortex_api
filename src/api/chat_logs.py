from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken

logs_api = APIRouter()


@logs_api.post('', status_code=201)
def create_log(logs: List[Schemas.ChatLog], db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    Crud.create_logs(db, logs)
    return {'message': f'success; added {len(logs)} new lines.'}


@logs_api.get('', response_model=List[Schemas.ChatLog])
def get_logs(
    query: str = '',
    steam_id: str = '',
    offset: int = 0,
    count: int = 25,
    start_time: datetime.datetime = datetime.datetime(2000, 1, 1),
    end_time: datetime.datetime = datetime.datetime(2100, 1, 1),
    db: Session = Depends(get_db)):
    return Crud.get_logs(db, query, steam_id, offset, count, start_time, end_time)