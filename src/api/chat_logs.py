from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session, Query
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken
from src.utils.pagination import PaginationParams, paginate, PaginatedResponse
from src.utils.cache import cache_manager


logs_api = APIRouter()


@logs_api.post('')
def create_log(logs: List[Schemas.ChatLog], db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    Crud.create_logs(db, logs)
    # Инвалидируем кэш логов после создания новых
    cache_manager.invalidate("logs:*")
    return {'message': f'success; added {len(logs)} new lines.'}


@logs_api.get('', response_model=PaginatedResponse[Schemas.ChatLog])
@cache_manager.cached(expire_time=300)  # кэшируем на 5 минут
async def get_logs(
    text: str = '',
    steam_id: str = '',
    nickname: str | None = None,
    server: str = '',
    pagination: PaginationParams = Depends(PaginationParams),
    start_time: datetime.datetime = datetime.datetime(2000, 1, 1),
    end_time: datetime.datetime = datetime.datetime(2100, 1, 1),
    db: Session = Depends(get_db)
):
    # Получаем общее количество записей для пагинации
    total = Crud.get_logs_count(
        db, text, steam_id, nickname, server, start_time, end_time
    )
    
    # Получаем записи с учетом пагинации
    logs = Crud.get_logs(
        db, text, steam_id, nickname, server,
        pagination.offset, pagination.page_size,
        start_time, end_time
    )
    
    # Формируем пагинированный ответ
    return paginate(logs, total, pagination)
