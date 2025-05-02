from fastapi import Depends, HTTPException, APIRouter
from src.database import models as Models
from src.database import crud as Crud
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import List, TypeVar
from src.api.tools import requireToken, get_db, getOrCreateUser, checkToken, getUser
from fastapi_filter import FilterDepends
from src.api.filter import Pagination

music_api = APIRouter()

T = TypeVar('T', bound=Models.IDModel)

def createObj(steam_id: str, schemaObj: Schemas.BaseModel, db: Session, token: str, model: type[T]) -> T:
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    obj = model(**(schemaObj.model_dump()), user=user)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def getObj(obj_id: int, db: Session, model: type[T]) -> T:
    if (obj := (db.query(model).filter(model.id == obj_id).first())) is None:
        raise HTTPException(404, f'Object ({model.__tablename__}) with id {obj_id} not found!')
    return obj

@music_api.get('/track/{steam_id}', response_model=Schemas.PlayerMusic.Output)
def get_track(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    track = Crud.get_player_music(db, user.id)
    if not track:
        raise HTTPException(status_code=404, detail="No track found for this user")
    return track

@music_api.put('/track/{steam_id}', response_model=Schemas.PlayerMusic.Output)
def update_track(
    steam_id: str,
    track_data: Schemas.PlayerMusic.Input,
    token: str = Depends(requireToken),
    db: Session = Depends(get_db)
):
    try:
        checkToken(db, token)
        user = getOrCreateUser(db, steam_id)
        
        if not track_data.soundname or track_data.soundname.strip() == "":
            raise HTTPException(status_code=400, detail="Field 'soundname' cannot be empty")
            
        if not track_data.path or track_data.path.strip() == "":
            raise HTTPException(status_code=400, detail="Field 'path' cannot be empty")
            
        track = Crud.set_player_music(db, user.id, track_data)
        return track
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error setting player music: {str(e)}")

@music_api.get('/list', response_model=List[Schemas.PlayerMusic.Output])
def get_all_tracks(
    pagination: Pagination = Depends(Pagination),
    search: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Get all music tracks with pagination and search.
    """
    if pagination.limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be less than or equal to 100.")
    tracks = Crud.get_all_music(db, pagination.offset, pagination.limit, search)
    return tracks

@music_api.get('/top', response_model=List[Schemas.PlayerMusic.Output])
def get_top_tracks(
    pagination: Pagination = Depends(Pagination),
    db: Session = Depends(get_db)
):
    if pagination.limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be less than or equal to 100.")
    tracks = Crud.get_top_music(db, pagination.limit)
    return tracks

@music_api.post('/track/{steam_id}/play')
def increment_track_plays(
    steam_id: str,
    token: str = Depends(requireToken),
    db: Session = Depends(get_db)
):
    checkToken(db, token)
    user = getUser(db, steam_id)
    track = Crud.increment_playcount_by_steam(db, user.id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found for this user")
    return {"status": "success"}

@music_api.delete('/track/{steam_id}')
def delete_track(
    steam_id: str,
    token: str = Depends(requireToken),
    db: Session = Depends(get_db)
):
    checkToken(db, token)
    user = getUser(db, steam_id)
    if Crud.delete_player_music(db, user.id):
        return {"status": "success", "message": "Track deleted"}
    raise HTTPException(status_code=404, detail="No track found for this user")

@music_api.get('/volume/{steam_id}', response_model=Schemas.PlayerVolume.Output)
def get_volume(steam_id: str, db: Session = Depends(get_db)):
    """
    Get player's music volume setting
    """
    user = getUser(db, steam_id)
    volume = Crud.get_player_volume(db, user.id)
    if not volume:
        volume = Crud.set_player_volume(db, user.id, Schemas.PlayerVolume.Input(volume=50))
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
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    volume = Crud.set_player_volume(db, user.id, volume_data)
    return volume