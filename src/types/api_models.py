import datetime
from pydantic import BaseModel

class StatusCode(BaseModel):
    status: int = 0

class User(BaseModel):
    id : int
    steamId : str

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
    user : User

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
    discord: bool = False




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
    

class Giveaway:
    class Input(BaseModel):
        activeUntil: datetime.datetime
        useCount: int = 1
        reward: int
    class Output(BaseModel):
        id: int
        user: User
        timeCreated: datetime.datetime
        activeUntil: datetime.datetime
        maxUseCount: int
        curUseCount: int
        reward: int
        status: int = 0
        
    

class L4D2Item:
    class Input(BaseModel):
        name: str
        command: str
    class Output(BaseModel):
        id: int
        name: str
        command: str

class PrivilegeItem:
    class Input(BaseModel):
        name: str
        privilegeTypeId: int
        duration: int #unix timestamp
    class Output(BaseModel):
        id: int
        name: str
        duration: int
        privilegeType: PrivilegeType

class Reward:
    class Input(BaseModel):
        name: str
        itemId: int | None
        privilegeItemId: int | None
    class Output(BaseModel):
        id: int
        name: str
        item: L4D2Item.Output | None
        privilegeItem: PrivilegeItem.Output | None

class SimpleQuest:
    class Input(BaseModel):
        name: str
        description: str
        rewardId: int
    class Output(BaseModel):
        id: int
        name: str
        description: str
        reward: Reward.Output

class DailyQuest:
    class Input(BaseModel):
        activeUntil: datetime.datetime
        curProgress: int = 0
        maxProgress: int = 1
        questId: int
    class Output(BaseModel):
        id: int
        user: User
        activeUntil: datetime.datetime
        curProgress: int
        maxProgress: int
        quest: SimpleQuest.Output
        rewards: list[Reward.Output]
        

class InventoryItem:
    class Input(BaseModel):
        itemId: int
        activeUntil: datetime.datetime
    class Output(BaseModel):
        id: int
        user: User
        item: L4D2Item.Output
        activeUntil: datetime.datetime
        

class EmptyDrop:
    class Output(BaseModel):
        user: User
        value: int
        nextDrop: datetime.datetime




class TopOutput(BaseModel):
    steamId: str
    agression: int
    support: int
    perks: int
    total: int



class PlayerSummary(BaseModel):
    steamid: str
    communityvisibilitystate: int | None = None
    profilestate: int | None = None
    personaname: str
    commentpermission: int | None = None
    profileurl: str
    avatar: str
    avatarmedium: str
    avatarfull: str | None = None
    avatarhash: str | None = None
    lastlogoff: int | None = None
    personastate: int | None = None
    realname: str | None = None
    primaryclanid: str | None = None
    timecreated: int | None = None
    personastateflags: int | None = None
    loccountrycode: str | None = None
    locstatecode: str | None = None


class BulkProfileInfo(BaseModel):
    steamInfo: PlayerSummary
    rank: int | None
    balance: int
    perks: PerkSet | None
    privileges: list[PrivilegeStatus]
    discordId: int | None

class Rank(BaseModel):
    rank: int
    score: int



class ServerPlayer(BaseModel):
    id: int
    name: str
    ip: str
    time: float = 0
    steamId: str
class ServerInfo(BaseModel):
    id: int
    name: str
    map: str
    playersCount: int
    maxPlayersCount: int
    ping: float
    ip: str
    port: int | str
    keywords: str | None
    time: datetime.datetime
    players: list[ServerPlayer]

class GroupInfo(BaseModel):
    membersCount: int
    membersInGame: int
    membersOnline: int


class PrivilegedUserInfo(BaseModel):
    steamId: str
    privilege: PrivilegeType
    steamInfo: PlayerSummary