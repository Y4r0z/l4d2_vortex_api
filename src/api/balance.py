from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken
import numpy as np

DROP_COOLDOWN = datetime.timedelta(hours=6)
DROP_VALUE_MIN = 100
DROP_VALUE_LOC = 400
DROP_VALUE_SCALE = 300

balance_api = APIRouter()

def getOrCreateBalance(db: Session, user: Models.User):
    if db.query(Models.Balance).filter(Models.Balance.userId == user.id).first() is None:
        db.add(Models.Balance(user=user, value=0))
    db.commit()
    db.refresh(user)
    return user.balance



@balance_api.get('', response_model=Schemas.Balance)
def get_balance(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    balance = getOrCreateBalance(db, user)
    return balance

@balance_api.post('/add', response_model=Schemas.Transaction)
def add_balance(steam_id: str, value: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    user = getUser(db, steam_id)
    balance = getOrCreateBalance(db, user)
    balance.value += value
    transaction = Models.Transaction(balance=balance, value=value, description='add')
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

@balance_api.post('/set', response_model=Schemas.Transaction)
def set_balance(steam_id: str, value: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    user = getUser(db, steam_id)
    balance = getOrCreateBalance(db, user)
    balance.value = value
    transaction = Models.Transaction(balance=balance, value=value, description='set')
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

@balance_api.post('/pay', response_model=Schemas.DuplexTransaction)
def pay_balance(source_steam_id: str, target_steam_id: str, value: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    if value < 0: raise HTTPException(400, f"Value must be positive!")
    checkToken(db, token)
    source = getUser(db, source_steam_id)
    target = getUser(db, target_steam_id)
    sourceBalance = getOrCreateBalance(db, source)
    targetBalance = getOrCreateBalance(db, target)
    if sourceBalance.value < value: raise HTTPException(400, f"Source <{source_steam_id}> doesn't have enough money to pay")
    sourceBalance.value -= value
    targetBalance.value += value
    transaction = Models.DuplexTransaction(source=sourceBalance, target=targetBalance, value=value, description='pay')
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@balance_api.get('/drop', response_model=Schemas.MoneyDrop)
def drop_money(steam_id: str, db: Session = Depends(get_db)):
    user = getOrCreateUser(db, steam_id)
    lastDrop = db.query(Models.MoneyDrop).filter(Models.MoneyDrop.userId == user.id).order_by(Models.MoneyDrop.time.desc()).first()
    if lastDrop is not None and (lastDrop.time + DROP_COOLDOWN > datetime.datetime.now()):
        return {'nextDrop':lastDrop.time + DROP_COOLDOWN, 'value':0, 'user':{'steamId': user.steamId, 'id':user.id}}
    balance = getOrCreateBalance(db, user)
    value = max(DROP_VALUE_MIN, int(np.random.normal(loc=DROP_VALUE_LOC, scale=DROP_VALUE_SCALE)))
    time = datetime.datetime.now()
    dropObj = Models.MoneyDrop(user=user, value=value, time=time)
    transaction = Models.Transaction(balance=balance, value=value, time=time, description='drop')
    balance.value += value
    db.add(dropObj)
    db.add(transaction)
    db.commit()
    return {'nextDrop':time + DROP_COOLDOWN, 'value':value, 'user':{'steamId': user.steamId, 'id':user.id}}
