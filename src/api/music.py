from fastapi import Depends, HTTPException, APIRouter
from src.database import models as Models
from src.database import crud as Crud
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import List, TypeVar
from src.api.tools import requireToken, get_db, getOrCreateUser, checkToken, getUser
from fastapi_filter import FilterDepends
from src.api.filter import Pagination
from src.services.logger import api_logger

music_api = APIRouter()

T = TypeVar('T', bound=Models.IDModel)

def createObj(steam_id: str, schemaObj: Schemas.BaseModel, db: Session, token: str, model: type[T]) -> T:
    context = {"steam_id": steam_id, "model": model.__name__}
    api_logger.info(f"Создание объекта {model.__name__} для пользователя {steam_id}", context=context)
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    obj = model(**(schemaObj.model_dump()), user=user)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    context["object_id"] = obj.id
    api_logger.info(f"Объект {model.__name__} с ID {obj.id} создан для пользователя {steam_id}", context=context)
    return obj

def getObj(obj_id: int, db: Session, model: type[T]) -> T:
    context = {"object_id": obj_id, "model": model.__name__}
    api_logger.info(f"Получение объекта {model.__name__} с ID {obj_id}", context=context)
    if (obj := (db.query(model).filter(model.id == obj_id).first())) is None:
        api_logger.warning(f"Объект {model.__name__} с ID {obj_id} не найден", context=context)
        raise HTTPException(404, f'Object ({model.__tablename__}) with id {obj_id} not found!')
    return obj

@music_api.get('/track/{steam_id}', response_model=Schemas.PlayerMusic.Output)
def get_track(steam_id: str, db: Session = Depends(get_db)):
    context = {"steam_id": steam_id, "endpoint": "get_track"}
    api_logger.info(f"Запрос трека для пользователя {steam_id}", context=context)
    user = getUser(db, steam_id)
    track = Crud.get_player_music(db, user.id)
    if not track:
        api_logger.warning(f"Трек для пользователя {steam_id} не найден", context=context)
        raise HTTPException(status_code=404, detail="No track found for this user")
    api_logger.info(f"Трек для пользователя {steam_id} успешно получен", context=context)
    return track

@music_api.put('/track/{steam_id}', response_model=Schemas.PlayerMusic.Output)
def update_track(
    steam_id: str,
    track_data: Schemas.PlayerMusic.Input,
    token: str = Depends(requireToken),
    db: Session = Depends(get_db)
):
    context = {"steam_id": steam_id, "endpoint": "update_track"}
    api_logger.info(f"Обновление трека для пользователя {steam_id}", context=context)
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    track = Crud.set_player_music(db, user.id, track_data)
    context["track_id"] = track.id
    api_logger.info(f"Трек для пользователя {steam_id} успешно обновлен", context=context)
    return track

@music_api.get('/list', response_model=List[Schemas.PlayerMusic.Output])
def get_all_tracks(
    pagination: Pagination = Depends(Pagination),
    search: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Get all music tracks with pagination and search.
    """
    context = {
        "endpoint": "get_all_tracks",
        "offset": pagination.offset,
        "limit": pagination.limit,
        "search": search
    }
    api_logger.info(f"Запрос списка треков с offset={pagination.offset}, limit={pagination.limit}, search={search}", context=context)
    if pagination.limit > 100:
        api_logger.warning(f"Превышен лимит запроса: {pagination.limit} > 100", context=context)
        raise HTTPException(status_code=400, detail="Limit must be less than or equal to 100.")
    tracks = Crud.get_all_music(db, pagination.offset, pagination.limit, search)
    context["tracks_count"] = len(tracks)
    api_logger.info(f"Получено {len(tracks)} треков", context=context)
    return tracks

@music_api.get('/top', response_model=List[Schemas.PlayerMusic.Output])
def get_top_tracks(
    pagination: Pagination = Depends(Pagination),
    db: Session = Depends(get_db)
):
    context = {"endpoint": "get_top_tracks", "limit": pagination.limit}
    api_logger.info(f"Запрос топ треков с limit={pagination.limit}", context=context)
    if pagination.limit > 100:
        api_logger.warning(f"Превышен лимит запроса: {pagination.limit} > 100", context=context)
        raise HTTPException(status_code=400, detail="Limit must be less than or equal to 100.")
    tracks = Crud.get_top_music(db, pagination.limit)
    context["tracks_count"] = len(tracks)
    api_logger.info(f"Получено {len(tracks)} топ треков", context=context)
    return tracks

@music_api.post('/track/{steam_id}/play')
def increment_track_plays(
    steam_id: str,
    token: str = Depends(requireToken),
    db: Session = Depends(get_db)
):
    context = {"steam_id": steam_id, "endpoint": "increment_track_plays"}
    api_logger.info(f"Увеличение счетчика проигрываний для пользователя {steam_id}", context=context)
    checkToken(db, token)
    user = getUser(db, steam_id)
    track = Crud.increment_playcount_by_steam(db, user.id)
    if not track:
        api_logger.warning(f"Трек для пользователя {steam_id} не найден", context=context)
        raise HTTPException(status_code=404, detail="Track not found for this user")
    context["track_id"] = track.id
    api_logger.info(f"Счетчик проигрываний для пользователя {steam_id} увеличен", context=context)
    return {"status": "success"}

@music_api.delete('/track/{steam_id}')
def delete_track(
    steam_id: str,
    token: str = Depends(requireToken),
    db: Session = Depends(get_db)
):
    context = {"steam_id": steam_id, "endpoint": "delete_track"}
    api_logger.info(f"Удаление трека для пользователя {steam_id}", context=context)
    checkToken(db, token)
    user = getUser(db, steam_id)
    if Crud.delete_player_music(db, user.id):
        api_logger.info(f"Трек для пользователя {steam_id} успешно удален", context=context)
        return {"status": "success", "message": "Track deleted"}
    api_logger.warning(f"Трек для пользователя {steam_id} не найден", context=context)
    raise HTTPException(status_code=404, detail="No track found for this user")

@music_api.get('/volume/{steam_id}', response_model=Schemas.PlayerVolume.Output)
def get_volume(steam_id: str, db: Session = Depends(get_db)):
    """
    Get player's music volume setting
    """
    context = {"steam_id": steam_id, "endpoint": "get_volume"}
    api_logger.info(f"Запрос громкости для пользователя {steam_id}", context=context)
    user = getUser(db, steam_id)
    volume = Crud.get_player_volume(db, user.id)
    if not volume:
        api_logger.info(f"Громкость для пользователя {steam_id} не найдена, устанавливаем значение по умолчанию (50)", context=context)
        volume = Crud.set_player_volume(db, user.id, Schemas.PlayerVolume.Input(volume=50))
    context["volume"] = volume.volume
    api_logger.info(f"Громкость для пользователя {steam_id} получена: {volume.volume}", context=context)
    return volume

@music_api.post('/volume/{steam_id}', response_model=Schemas.PlayerVolume.Output)
def set_volume(
    steam_id: str,
    volume_data: Schemas.PlayerVolume.Input,
    token: str = Depends(requireToken),
    db: Session = Depends(get_db)
):
    """
    Set player's music volume
    """
    context = {"steam_id": steam_id, "endpoint": "set_volume", "volume": volume_data.volume}
    api_logger.info(f"Установка громкости {volume_data.volume} для пользователя {steam_id}", context=context)
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    volume = Crud.set_player_volume(db, user.id, volume_data)
    api_logger.info(f"Громкость для пользователя {steam_id} установлена: {volume.volume}", context=context)
    return volume