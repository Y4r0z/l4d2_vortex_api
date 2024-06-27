from sqlalchemy.orm import Session
import src.database.models as Models
import src.types.api_models as Schemas
import src.database.predefined as Predefined
import datetime

def get_user(db: Session, steam_id : str):
    return db.query(Models.User).filter(Models.User.steamId == steam_id).first()

def create_user(db : Session, steam_id : str) -> Models.User:
    user = Models.User(steamId=steam_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_perks(db: Session, user_id : int) -> Models.PerkSet | None:
    return db.query(Models.PerkSet).filter(Models.PerkSet.userId == user_id).order_by(Models.PerkSet.time.desc()).first()

def set_perks(db:Session, user_id : int, perks : Schemas.PerkSet) -> Models.PerkSet:
    perkSet = Models.PerkSet(
        **perks.model_dump(),
        userId = user_id
    )
    db.add(perkSet)
    db.commit()
    db.refresh(perkSet)
    return perkSet

def check_token(db: Session, token : str):
    found = db.query(Models.AuthToken).filter(Models.AuthToken.token == token).first()
    return found is not None

def __checkPriv(db: Session, user_id: int, priv_id: int):
    prv = db.query(Models.PrivilegeStatus)\
        .filter(Models.PrivilegeStatus.privilegeId == priv_id, Models.PrivilegeStatus.userId == user_id)\
        .order_by(Models.PrivilegeStatus.activeUntil.desc()).first()
    if prv is None: return False
    return prv.activeUntil > datetime.datetime.now()

def get_privileges(db: Session, user_id : int) -> Schemas.PrivilegesList:
    prv = Schemas.PrivilegesList()
    prv.owner = __checkPriv(db, user_id, Predefined.PrivilegeTypes['owner'].id)
    prv.admin = __checkPriv(db, user_id, Predefined.PrivilegeTypes['admin'].id)
    prv.moderator = __checkPriv(db, user_id, Predefined.PrivilegeTypes['moderator'].id)
    prv.soundpad = __checkPriv(db, user_id, Predefined.PrivilegeTypes['soundpad'].id)
    prv.mediaPlayer = __checkPriv(db, user_id, Predefined.PrivilegeTypes['media_player'].id)
    prv.vip = __checkPriv(db, user_id, Predefined.PrivilegeTypes['vip'].id)
    return prv

def add_privilege(db: Session, user_id: int, priv_id : int, until : datetime.datetime) -> Models.PrivilegeStatus:
    priv = Models.PrivilegeStatus(userId=user_id, privilegeId=priv_id, activeUntil=until)
    db.add(priv)
    db.commit()
    db.refresh(priv)
    return priv