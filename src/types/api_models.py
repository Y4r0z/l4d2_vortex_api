import datetime
from pydantic import BaseModel

class PerkSet(BaseModel):
    survivorPerk1: str
    survivorPerk2: str
    survivorPerk3: str
    survivorPerk4: str

    boomerPerk: str
    smokerPerk: str
    hunterPerk: str
    jockeyPerk: str
    spitterPerk: str
    chargerPerk: str
    tankPerk: str

class PrivilegeType(BaseModel):
    id : int
    accessLevel : int = 100
    name : str
    description : str | None

class PrivilegeStatus(BaseModel):
    id : int
    privilege : PrivilegeType
    activeUntil : datetime.datetime
    userId : int

class PrivilegesList(BaseModel):
    owner: bool = False
    admin: bool = False
    moderator: bool = False
    soundpad: bool = False
    mediaPlayer: bool = False
    vip: bool = False
    premium: bool = False
    legend: bool = False
    customPrefix:str = ""
    welcomePhrase: str = ""

class User(BaseModel):
    id : int
    steamId : str


class Balance(BaseModel):
    id: int
    user: User
    value : int

class Transaction(BaseModel):
    id: int
    balance: Balance
    value: int
    description: str

class DuplexTransaction(BaseModel):
    id: int
    source: Balance
    target: Balance
    value: int
    description: str


    