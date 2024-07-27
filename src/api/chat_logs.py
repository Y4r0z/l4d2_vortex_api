from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session, Query
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken
from src.api.filter import LogsFilter, FilterDepends, Pagination


logs_api = APIRouter()


@logs_api.post('')
def create_log(logs: List[Schemas.ChatLog], db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    Crud.create_logs(db, logs)
    return {'message': f'success; added {len(logs)} new lines.'}


@logs_api.get('', response_model=List[Schemas.ChatLog])
def get_logs(
    text: str = '',
    steam_id: str = '',
    nickname: str = '',
    server: str = '',
    offset: int = 0,
    limit: int = 25,
    start_time: datetime.datetime = datetime.datetime(2000, 1, 1),
    end_time: datetime.datetime = datetime.datetime(2100, 1, 1),
    db: Session = Depends(get_db)):
    return Crud.get_logs(db, text, steam_id, nickname, server, offset, limit, start_time, end_time)

# @logs_api.get('', response_model=list[Schemas.ChatLog])
# def test_logs(
#     logs_filter: LogsFilter = FilterDepends(LogsFilter), 
#     db: Session = Depends(get_db), 
#     p: Pagination = Depends(Pagination)):
#     query = db.query(Models.ChatLog)
#     query = logs_filter.filter(query)
#     query = logs_filter.sort(query)
#     return query.offset(p.offset).limit(p.limit).all()