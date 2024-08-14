from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken, findByID, findByIDOrAbort, findByField, findByFieldOrAbort
from src.api.filter import L4D2ItemFilter, Pagination, PrivilegeItemFilter
from fastapi_filter import FilterDepends


DROP_COOLDOWN = datetime.timedelta(hours=12)

items_api = APIRouter()

@items_api.get('/drop', response_model=Schemas.EmptyDrop.Output)
def drop_item(steam_id: str, db: Session = Depends(get_db)):
    """
    Пустой дроп.\n
    value = 1 | 0;\n
    1 - если кулдаун прошел, 0 - если нет.
    """
    user = getOrCreateUser(db, steam_id)
    lastDrop = db.query(Models.EmptyDrop)\
        .filter(Models.EmptyDrop.userId == user.id)\
        .order_by(Models.EmptyDrop.time.desc())\
        .first()
    if lastDrop is not None and (lastDrop.time + DROP_COOLDOWN > datetime.datetime.now()):
        return {
            'nextDrop': lastDrop.time + DROP_COOLDOWN,
            'value': 0,
            'user': {'steam_id': user.steamId, 'id': user.id}
        }
    time = datetime.datetime.now()
    db.add(Models.EmptyDrop(user=user, time=time))
    db.commit()
    return {
        'nextDrop': time + DROP_COOLDOWN,
        'value': 1,
        'user': {'steam_id': user.steamId, 'id': user.id}
    }


@items_api.post('/l4d2_item', response_model=Schemas.L4D2Item.Output)
def create_l4d2_item(item: Schemas.L4D2Item.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    """
    Добавляет в базу данных предмет из L4D2.\n
    Принимает название предмета и команду, которая выдаст его.
    """
    checkToken(db, token)
    obj = Models.L4D2Item(name=item.name, command=item.command)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@items_api.get('/l4d2_item', response_model=Schemas.L4D2Item.Output)
def get_l4d2_item(item_id: int, db: Session = Depends(get_db)):
    """
    Выдает предмет по id.
    """
    return findByIDOrAbort(db, Models.L4D2Item, item_id)


@items_api.get('/l4d2_item/by_name', response_model=Schemas.L4D2Item.Output)
def get_l4d2_item_byname(item_name: str, db: Session = Depends(get_db)):
    """
    Выдает предмет по названию (первый подходящий).
    """
    return findByFieldOrAbort(db, Models.L4D2Item, Models.L4D2Item.name, item_name)

@items_api.get('/l4d2_item/search', response_model=List[Schemas.L4D2Item.Output])
def search_l4d2_items(db: Session = Depends(get_db), items_filter: L4D2ItemFilter = FilterDepends(L4D2ItemFilter), pagination: Pagination = Depends(Pagination)):
    query = db.query(Models.L4D2Item)
    query = items_filter.filter(query)
    query = items_filter.sort(query)
    query = pagination.paginate(query)
    return query.all()

@items_api.delete('/l4d2_item')
def delete_l4d2_item(item_id: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    """
    Удаляет предмет L4D2 из базы данных.
    """
    checkToken(db, token)
    db.delete(findByIDOrAbort(db, Models.L4D2Item, item_id))
    db.commit()
    return "Item deleted successfully"

@items_api.put('/l4d2_item', response_model=Schemas.L4D2Item.Output)
def change_l4d2_item(item_id: int, updated_item: Schemas.L4D2Item.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    """
    Изменяет данные предмета L4D2.
    """
    checkToken(db, token)
    item = findByIDOrAbort(db, Models.L4D2Item, item_id)
    item.name = updated_item.name
    item.command = updated_item.command
    db.commit()
    return item



@items_api.post('/privilege_item', response_model=Schemas.PrivilegeItem.Output)
def create_privilege_item(item: Schemas.PrivilegeItem.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    """
    Создает привелеиию, как предмет, который может быть выдан пользователю.
    """
    checkToken(db, token)
    findByIDOrAbort(db, Models.PrivilegeType, item.privilegeTypeId)
    db.add(obj:=Models.PrivilegeItem(name=item.name, duration=item.duration, privilegeTypeId=item.privilegeTypeId))
    db.commit()
    db.refresh(obj)
    return obj

@items_api.get('/privilege_item', response_model=Schemas.PrivilegeItem.Output)
def get_privilege_item(item_id: int, db: Session = Depends(get_db)):
    return findByIDOrAbort(db, Models.PrivilegeItem, item_id)

@items_api.delete('/privilege_item')
def delete_privilege_item(item_id: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    db.delete(findByIDOrAbort(db, Models.PrivilegeItem, item_id))
    db.commit()
    return "PrivilegeItem deleted successfully"

@items_api.put('/privilege_item', response_model=Schemas.PrivilegeItem.Output)
def change_privilege_item(item_id: int, updated_item: Schemas.PrivilegeItem.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    item = findByIDOrAbort(db, Models.PrivilegeItem, item_id)
    item.name = updated_item.name
    item.duration = updated_item.duration
    item.privilegeTypeId = updated_item.privilegeTypeId
    db.commit()
    return item

@items_api.get('/privilege_item/by_name', response_model=Schemas.PrivilegeItem.Output)
def get_privilege_item_byname(item_name: str, db: Session = Depends(get_db)):
    return findByFieldOrAbort(db, Models.PrivilegeItem, Models.PrivilegeItem.name, item_name)

@items_api.get('/privilege_item/search', response_model=List[Schemas.PrivilegeItem.Output])
def search_privilege_items(db: Session = Depends(get_db), items_filter: PrivilegeItemFilter = FilterDepends(PrivilegeItemFilter), pagination: Pagination = Depends(Pagination)):
    query = db.query(Models.PrivilegeItem)
    query = items_filter.filter(query)
    query = items_filter.sort(query)
    query = pagination.paginate(query)
    return query.all()
