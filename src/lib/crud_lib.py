from sqlalchemy.orm import Session
from typing import TypeVar, Type, Dict, Any
from src.database import models as Models
import src.types.api_models as Schemas

T = TypeVar('T', bound=Models.IDModel)

class CrudService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_stats_record(self, model: Type[T], user_id: int) -> T:
        record = self.db.query(model).filter(model.userId == user_id).first()
        if not record:
            record = model(userId=user_id)
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
        return record
    
    def add_stats_data(self, model: Type[T], user_id: int, data: Dict[str, Any]) -> T:
        record = self.get_or_create_stats_record(model, user_id)
        
        for field, value in data.items():
            if hasattr(record, field):
                current_value = getattr(record, field)
                setattr(record, field, current_value + value)
        
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def replace_stats_data(self, model: Type[T], user_id: int, data: Dict[str, Any]) -> T:
        record = self.get_or_create_stats_record(model, user_id)
        
        for field, value in data.items():
            if hasattr(record, field) and value is not None:
                setattr(record, field, value)
        
        self.db.commit()
        self.db.refresh(record)
        return record

def createObj(steam_id: str, schemaObj: Schemas.BaseModel, db: Session, token: str, model: type[T]) -> T:
    from src.lib.core import checkToken, getOrCreateUser
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    obj = model(**(schemaObj.model_dump()), user=user)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def getObj(obj_id: int, db: Session, model: type[T]) -> T:
    from fastapi import HTTPException
    if (obj := (db.query(model).filter(model.id == obj_id).first())) is None:
        raise HTTPException(404, f'Object ({model.__tablename__}) with id {obj_id} not found!')
    return obj