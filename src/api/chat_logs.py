from fastapi import Depends, HTTPException, APIRouter, Query
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken
from src.services.logger import api_logger
logs_api = APIRouter()
@logs_api.post('')
async def create_log(
    logs: List[Schemas.ChatLog],
    db: Session = Depends(get_db),
    token: str = Depends(requireToken)
):
    """
    Создает новые записи логов чата
    """
    try:
        checkToken(db, token)
        
        Crud.create_logs(db, logs)
        return {'message': f'success; added {len(logs)} new lines.'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred when creating logs"
        )
@logs_api.get('', response_model=List[Schemas.ChatLog])
async def get_logs(
    text: str = Query('', description="Текст для поиска в сообщениях"),
    steam_id: str = Query('', description="SteamID для фильтрации"),
    nickname: str = Query(None, description="Никнейм для фильтрации"),
    server: str = Query('', description="Имя сервера для фильтрации"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(25, ge=1, le=100, description="Количество записей на страницу"),
    start_time: datetime.datetime = Query(
        default=datetime.datetime(2000, 1, 1),
        description="Начало временного диапазона"
    ),
    end_time: datetime.datetime = Query(
        default=datetime.datetime.now() + datetime.timedelta(days=1),
        description="Конец временного диапазона"
    ),
    db: Session = Depends(get_db)
):
    """
    Получает логи чата с возможностью фильтрации и пагинации
    """
    try:
        logs = Crud.get_logs(db, text, steam_id, nickname, server, offset, limit, start_time, end_time)
        
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve chat logs due to server error"
        )