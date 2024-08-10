from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken, findByID, findByIDOrAbort, findByField, findByFieldOrAbort
from src.api.filter import L4D2ItemFilter, Pagination, UserInventoryFilter
from fastapi_filter import FilterDepends

inventory_api = APIRouter()

@inventory_api.post('/add', response_model=Schemas.InventoryItem.Output)
def add_item(steam_id: str, invitem: Schemas.InventoryItem.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    """
    Добавляет предмет в инвентарь пользователя.
    """
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    db.add(inv := Models.UserInventory(user=user, itemId=invitem.itemId, activeUntil=invitem.activeUntil))
    db.commit()
    db.refresh(inv)
    return inv

@inventory_api.get('/items', response_model=List[Schemas.InventoryItem.Output])
def get_inventory_items(steam_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список предметов в инвентаре пользователя.
    """
    user = getUser(db, steam_id)
    db.query(Models.UserInventory).filter(Models.UserInventory.userId == user.id).filter(Models.UserInventory.activeUntil < datetime.datetime.now(tz=datetime.timezone.utc)).delete()
    db.commit()
    db.refresh(user)
    return db.query(Models.UserInventory).filter(Models.UserInventory.userId == user.id).all()


@inventory_api.delete('')
def delete_inventory_item(inventory_item_id: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    """
    Удаляет предмет из любого инвентаря.
    """
    checkToken(db, token)
    db.delete(findByIDOrAbort(db, Models.UserInventory, inventory_item_id))
    db.commit()
    return "Item deleted successfully"

@inventory_api.post('/checkout', response_model=Schemas.L4D2Item.Output)
def checkout_item(inventory_item_id: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    """
    Выдаёт предмет из инвентаря пользователя (при этом он считается истекшим).
    """
    checkToken(db, token)
    inv_item = findByIDOrAbort(db, Models.UserInventory, inventory_item_id)
    if inv_item.activeUntil.replace(tzinfo=datetime.timezone.utc) < datetime.datetime.now(tz=datetime.timezone.utc):
        raise HTTPException(status_code=400, detail="Item is expired")
    inv_item.activeUntil = datetime.datetime.now(tz=datetime.timezone.utc)
    db.commit()
    db.refresh(inv_item)
    return inv_item.item


@inventory_api.get('', response_model=Schemas.InventoryItem.Output)
def get_inventory_item(inventory_item_id: int, db: Session = Depends(get_db)):
    """
    Возвращает предмет из любого инвентаря.
    """
    return findByIDOrAbort(db, Models.UserInventory, inventory_item_id)


@inventory_api.get('/search', response_model=List[Schemas.InventoryItem.Output])
def inventory_search(
    db: Session = Depends(get_db), 
    user_inventory_filter: UserInventoryFilter = FilterDepends(UserInventoryFilter), 
    pagination: Pagination = Depends(Pagination)
):
    query = db.query(Models.UserInventory)
    query = query.join(Models.User)
    query = user_inventory_filter.filter(query)
    query = query.join(Models.L4D2Item)
    query = user_inventory_filter.filter(query)
    query = user_inventory_filter.sort(query)
    query = pagination.paginate(query)
    return query.all()
    

    