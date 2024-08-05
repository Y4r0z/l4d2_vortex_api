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

class SteamDiscordLink(BaseModel):
    id: int
    discordId: str
    user: User

class ChatLog(BaseModel):
    id: int = 0
    steamId: str
    nickname: str | None = None
    text: str
    time: datetime.datetime
    server: str = 'None'
    team: int = 0
    chatTeam: int = 0




class RoundScore:
    class Input(BaseModel):
        agression: int = 0
        support: int = 0
        perks: int = 0
        team: int = 0
        time: datetime.datetime | None = None
    class Output(BaseModel):
        id: int
        user: User
        agression: int
        support: int
        perks: int
        team: int
        time: datetime.datetime

class ScoreSeason:
    class Output(BaseModel):
        id: int
        user: User
        agression: int
        support: int 
        perks: int
        date: datetime.date

class PlaySession:
    class Input(BaseModel):
        timeFrom: datetime.datetime
        timeTo: datetime.datetime | None = None
    class Output(BaseModel):
        id: int
        user: User
        timeFrom: datetime.datetime
        timeTo: datetime.datetime




class MoneyDrop(BaseModel):
    user: User
    value: int
    nextDrop: datetime.datetime
    

