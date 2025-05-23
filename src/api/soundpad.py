from fastapi import Depends, HTTPException, APIRouter
from src.database import models as Models
from src.database import crud as Crud
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import List
from src.lib.tools_lib import requireToken, get_db, checkToken

soundpad_api = APIRouter()

@soundpad_api.get('/list', response_model=List[Schemas.PlayerSound.Output])
def get_sounds(db: Session = Depends(get_db)):
    sounds = Crud.get_player_sounds(db)
    return sounds

@soundpad_api.post('/add', response_model=Schemas.PlayerSound.Output)
def add_sound(
    sound_data: Schemas.PlayerSound.Input,
    token: str = Depends(requireToken),
    db: Session = Depends(get_db)
):
    try:
        checkToken(db, token)
        
        if not sound_data.soundname or sound_data.soundname.strip() == "":
            raise HTTPException(status_code=400, detail="Field 'soundname' cannot be empty")
            
        if not sound_data.path or sound_data.path.strip() == "":
            raise HTTPException(status_code=400, detail="Field 'path' cannot be empty")
            
        sound = Crud.add_player_sound(db, sound_data)
        return sound
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding sound: {str(e)}")

@soundpad_api.delete('/{sound_id}')
def delete_sound(
    sound_id: int,
    token: str = Depends(requireToken),
    db: Session = Depends(get_db)
):
    checkToken(db, token)
    if Crud.delete_player_sound(db, sound_id):
        return {"status": "success", "message": "Sound deleted"}
    raise HTTPException(status_code=404, detail="Sound not found")

@soundpad_api.post('/{sound_id}/play')
def increment_playcount(
    sound_id: int,
    token: str = Depends(requireToken),
    db: Session = Depends(get_db)
):
    checkToken(db, token)
    sound = Crud.increment_sound_playcount(db, sound_id)
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")
    return {"status": "success", "playcount": sound.playcount}