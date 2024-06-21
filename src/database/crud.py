from sqlalchemy.orm import Session
import src.database.models as Models
import src.types.api_models as Schemas

def get_user(db: Session, steam_id : str):
    return db.query(Models.User).filter(Models.User.steamId == steam_id).first()

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

def get_privilege(db: Session, user_id : int) -> Models.PrivilegeType:
    return db.query(Models.PrivilegeStatus).filter(Models.PrivilegeStatus.userId == user_id).first()
