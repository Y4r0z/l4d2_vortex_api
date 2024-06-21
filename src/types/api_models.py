import datetime
from pydantic import BaseModel

class PerkSet(BaseModel):
    survivorPerk1: int = 0
    survivorPerk2: int = 0
    survivorPerk3: int = 0
    survivorPerk4: int = 0

    boomerPerk: int = 0
    smokerPerk: int = 0
    hunterPerk: int = 0
    jockeyPerk: int = 0
    spitterPerk: int = 0
    chargerPerk: int = 0
    tankPerk: int = 0

class PrivilegeType(BaseModel):
    accessLevel : int = 100
    name : str
    description : str | None

class PrivilegeStatus(BaseModel):
    privilege : PrivilegeType
    activeUntil : datetime.datetime
    userId : int


    