from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken


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

