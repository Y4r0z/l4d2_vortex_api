from fastapi import Depends, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List, Union
import datetime
from src.lib.tools_lib import getUser, requireToken, get_db, getOrCreateUser, checkToken, getOrCreateBalance
import numpy as np

DROP_COOLDOWN = datetime.timedelta(hours=6)
DROP_VALUE_MIN = 100
DROP_VALUE_LOC = 400
DROP_VALUE_SCALE = 300

balance_api = APIRouter()

@balance_api.get('', response_model=Schemas.Balance)
def get_balance(steam_id: str, db: Session = Depends(get_db)):
    try:
        user = getUser(db, steam_id)
        balance = getOrCreateBalance(db, user)
        
        return balance
    except Exception as e:
        raise

@balance_api.post('/add', response_model=Schemas.Transaction)
def add_balance(steam_id: str, value: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    try:
        checkToken(db, token)
        user = getOrCreateUser(db, steam_id)
        balance = getOrCreateBalance(db, user)
        
        old_value = balance.value
        balance.value += value
        
        transaction = Models.Transaction(balance=balance, value=value, description='add')
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    except Exception as e:
        raise

@balance_api.post('/set', response_model=Schemas.Transaction)
def set_balance(steam_id: str, value: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    try:
        checkToken(db, token)
        user = getOrCreateUser(db, steam_id)
        balance = getOrCreateBalance(db, user)
        
        old_value = balance.value
        balance.value = value
        
        transaction = Models.Transaction(balance=balance, value=value, description='set')
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    except Exception as e:
        raise

@balance_api.post('/pay', response_model=Schemas.DuplexTransaction)
def pay_balance(source_steam_id: str, target_steam_id: str, value: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    try:
        if value < 0:
            raise HTTPException(400, f"Value must be positive!")
            
        checkToken(db, token)
        source = getUser(db, source_steam_id)
        target = getOrCreateUser(db, target_steam_id)
        sourceBalance = getOrCreateBalance(db, source)
        targetBalance = getOrCreateBalance(db, target)
        
        if sourceBalance.value < value:
            raise HTTPException(400, f"Source <{source_steam_id}> doesn't have enough money to pay")
            
        source_old = sourceBalance.value
        target_old = targetBalance.value
        
        sourceBalance.value -= value
        targetBalance.value += value
        
        transaction = Models.DuplexTransaction(source=sourceBalance, target=targetBalance, value=value, description='pay')
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        raise

@balance_api.get('/drop', response_model=Schemas.MoneyDrop)
def drop_money(steam_id: str, db: Session = Depends(get_db)):
    try:
        user = getOrCreateUser(db, steam_id)
        lastDrop = db.query(Models.MoneyDrop).filter(Models.MoneyDrop.userId == user.id).order_by(Models.MoneyDrop.time.desc()).first()
        
        if lastDrop is not None and (lastDrop.time + DROP_COOLDOWN > datetime.datetime.now()):
            next_drop_time = lastDrop.time + DROP_COOLDOWN
            return {'nextDrop':lastDrop.time + DROP_COOLDOWN, 'value':0, 'user':{'steamId': user.steamId, 'id':user.id}}
            
        balance = getOrCreateBalance(db, user)
        value = max(DROP_VALUE_MIN, int(np.random.normal(loc=DROP_VALUE_LOC, scale=DROP_VALUE_SCALE)))
        time = datetime.datetime.now()
        
        old_balance = balance.value
        dropObj = Models.MoneyDrop(user=user, value=value, time=time)
        transaction = Models.Transaction(balance=balance, value=value, time=time, description='drop')
        balance.value += value
        
        db.add(dropObj)
        db.add(transaction)
        db.commit()
        
        return {'nextDrop':time + DROP_COOLDOWN, 'value':value, 'user':{'steamId': user.steamId, 'id':user.id}}
    except Exception as e:
        raise

@balance_api.post('/giveaway', response_model=Union[Schemas.Giveaway.Output, Schemas.StatusCode])
def create_giveaway(steam_id: str, info: Schemas.Giveaway.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    try:
        checkToken(db, token)
        user = getOrCreateUser(db, steam_id)
        balance = getOrCreateBalance(db, user)
        
        if info.reward <= 0:
            return JSONResponse({'status': 1}, status_code=400)
            
        if balance.value < info.reward * info.useCount:
            return JSONResponse({'status': 2}, status_code=400)
            
        if info.activeUntil.replace(tzinfo=datetime.timezone.utc) <= datetime.datetime.now(tz=datetime.timezone.utc):
            return JSONResponse({'status': 3}, status_code=400)
            
        if info.useCount < 1:
            return JSONResponse({'status': 4}, status_code=400)
            
        total_cost = info.reward * info.useCount
        old_balance = balance.value
        balance.value -= total_cost
        
        obj = Models.Giveaway(user=user, activeUntil=info.activeUntil, maxUseCount=info.useCount, reward=info.reward)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        
        return obj
    except Exception as e:
        raise

@balance_api.get('/giveaway/checkout', response_model=Union[Schemas.Giveaway.Output, Schemas.StatusCode])
def checkout_giveaway(giveaway_id: int, steam_id: str, db: Session = Depends(get_db)):
    try:
        user = getOrCreateUser(db, steam_id)
        balance = getOrCreateBalance(db, user)
        giveaway = db.query(Models.Giveaway).filter(Models.Giveaway.id == giveaway_id).first()
        
        if giveaway is None:
            return JSONResponse({'status': 1}, status_code=400)
            
        if giveaway.userId == user.id:
            return JSONResponse({'status': 5}, status_code=400)
            
        if datetime.datetime.now() > giveaway.activeUntil:
            return JSONResponse({'status': 2}, status_code=400)
            
        if giveaway.curUseCount >= giveaway.maxUseCount:
            return JSONResponse({'status': 3}, status_code=400)
            
        existing_use = db.query(Models.GiveawayUse)\
            .filter((Models.GiveawayUse.userId == user.id) & (Models.GiveawayUse.giveawayId == giveaway.id))\
            .first()
            
        if existing_use is not None:
            return JSONResponse({'status': 4}, status_code=400)
            
        gu = Models.GiveawayUse(user=user, giveaway=giveaway)
        giveaway.curUseCount += 1
        
        old_balance = balance.value
        balance.value += giveaway.reward
        
        db.add(gu)
        db.commit()
        db.refresh(giveaway)
        
        return giveaway
    except Exception as e:
        raise

@balance_api.delete('/giveaway')
def delete_giveaway(giveaway_id: int, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    try:
        checkToken(db, token)
        giveaway = db.query(Models.Giveaway).filter(Models.Giveaway.id == giveaway_id).first()
        
        if giveaway is None:
            raise HTTPException(404, 'Giveaway not found')
            
        balance = getOrCreateBalance(db, giveaway.user)
        refund_amount = giveaway.reward * (giveaway.maxUseCount - giveaway.curUseCount)
        old_balance = balance.value
        
        balance.value += refund_amount
        
        db.delete(giveaway)
        db.commit()
        
        return 'Deleted'
    except HTTPException:
        raise
    except Exception as e:
        raise

@balance_api.get('/giveaway/all', response_model=list[Schemas.Giveaway.Output])
def get_giveaways_by_steam(steam_id: str, db: Session = Depends(get_db)):
    try:
        user = getUser(db, steam_id)
        now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
        
        giveaways = db.query(Models.Giveaway) \
            .filter(Models.Giveaway.userId == user.id) \
            .filter((now < Models.Giveaway.activeUntil) & (Models.Giveaway.curUseCount < Models.Giveaway.maxUseCount)).all()
            
        return giveaways
    except Exception as e:
        raise