import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional

class StatusCode(BaseModel):
    status: int = 0

class User(BaseModel):
    id : int
    steamId : str

class ServerPlayer(BaseModel):
    userId: int
    name: str
    ip: str
    time: float
    steamId: str

class ServerStatus(BaseModel):
    id: int
    name: str
    map: str
    players: int
    maxPlayers: int
    ip: str
    port: int
    mode: str
    players: List[ServerPlayer] = []

class ServerUpdateRequest(BaseModel):
    name: str
    map: str
    mode: str
    max_slots: int
    ip: str
    port: int
    players: List[Dict[str, Any]]


class QueueJoinRequest(BaseModel):
    clientId: str
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)

class QueueLeaveRequest(BaseModel):
    clientId: str

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

class PlayTime(BaseModel):
    steam_id: str
    total_seconds: int
    total_hours: float

class TopPlaytime(BaseModel):
    rank: int
    steam_id: str
    total_seconds: int
    total_hours: float

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


class PlayerMusic:
    class Input(BaseModel):
        soundname: str = Field(..., min_length=1)
        path: str = Field(..., min_length=1)
        url: str | None = None
        nick: str | None = None
        
        @field_validator('soundname', 'path')
        @classmethod
        def validate_non_empty(cls, v):
            if v is not None and v.strip() == '':
                raise ValueError("Field cannot be empty or contain only whitespace")
            return v
            
    class Output(BaseModel):
        id: int
        soundname: str
        path: str
        url: str
        nick: str = None
        playcount: int
        updated_at: datetime.datetime
        user: User

class PlayerVolume:
    class Input(BaseModel):
        volume: int
    
    class Output(BaseModel):
        id: int
        volume: int
        updated_at: datetime.datetime
        user: User

class PlayerSound:
    class Input(BaseModel):
        soundname: str = Field(..., min_length=1)
        path: str = Field(..., min_length=1)
        cooldown: float
        
        @field_validator('soundname', 'path')
        @classmethod
        def validate_non_empty(cls, v):
            if v is not None and v.strip() == '':
                raise ValueError("Field cannot be empty or contain only whitespace")
            return v
    
    class Output(BaseModel):
        id: int
        soundname: str
        path: str
        cooldown: float
        playcount: int

class StPlayerBase:
    class Input(BaseModel):
        last_nickname: Optional[str] = None
        last_online: Optional[str] = None
        last_ip: Optional[str] = None
        last_country: Optional[str] = None
        last_city: Optional[str] = None
        last_region: Optional[str] = None
    
    class Output(BaseModel):
        id: int
        user: User
        last_nickname: Optional[str] = None
        last_online: Optional[str] = None
        last_ip: Optional[str] = None
        last_country: Optional[str] = None
        last_city: Optional[str] = None
        last_region: Optional[str] = None

class StPlayerHits:
    class Input(BaseModel):
        NULL_HITBOX: int = 0
        HEAD: int = 0
        CHEST: int = 0
        STOMACH: int = 0
        LEFT_ARM: int = 0
        RIGHT_ARM: int = 0
        LEFT_LEG: int = 0
        RIGHT_LEG: int = 0
    
    class Output(BaseModel):
        id: int
        user: User
        NULL_HITBOX: int = 0
        HEAD: int = 0
        CHEST: int = 0
        STOMACH: int = 0
        LEFT_ARM: int = 0
        RIGHT_ARM: int = 0
        LEFT_LEG: int = 0
        RIGHT_LEG: int = 0

class StPlayerKills:
    class Input(BaseModel):
        survivor_killed: int = 0
        infected_killed: int = 0
        smoker_killed: int = 0
        boomer_killed: int = 0
        hunter_killed: int = 0
        spitter_killed: int = 0
        jockey_killed: int = 0
        charger_killed: int = 0
        witch_killed: int = 0
        tank_killed: int = 0
    
    class Output(BaseModel):
        id: int
        user: User
        survivor_killed: int = 0
        infected_killed: int = 0
        smoker_killed: int = 0
        boomer_killed: int = 0
        hunter_killed: int = 0
        spitter_killed: int = 0
        jockey_killed: int = 0
        charger_killed: int = 0
        witch_killed: int = 0
        tank_killed: int = 0

class StPlayerShots:
    class Input(BaseModel):
        player_death: int = 0
        player_fire: int = 0
        player_hits: int = 0
        player_heads: int = 0
        player_damage: int = 0
        player_hurt: int = 0
    
    class Output(BaseModel):
        id: int
        user: User
        player_death: int = 0
        player_fire: int = 0
        player_hits: int = 0
        player_heads: int = 0
        player_damage: int = 0
        player_hurt: int = 0

class StPlayerWeapon:
    class Input(BaseModel):
        pistol: int = 0
        pistol_magnum: int = 0
        autoshotgun: int = 0
        shotgun_chrome: int = 0
        pumpshotgun: int = 0
        shotgun_spas: int = 0
        smg: int = 0
        smg_mp5: int = 0
        smg_silenced: int = 0
        rifle_ak47: int = 0
        rifle_sg552: int = 0
        rifle: int = 0
        rifle_m60: int = 0
        rifle_desert: int = 0
        hunting_rifle: int = 0
        sniper_military: int = 0
        sniper_awp: int = 0
        sniper_scout: int = 0
        weapon_grenade_launcher: int = 0
        molotov: int = 0
        pipe_bomb: int = 0
        vomitjar: int = 0
        melee: int = 0
        baseball_bat: int = 0
        cricket_bat: int = 0
        crowbar: int = 0
        electric_guitar: int = 0
        fireaxe: int = 0
        frying_pan: int = 0
        katana: int = 0
        knife: int = 0
        machete: int = 0
        tonfa: int = 0
        pain_pills: int = 0
        adrenaline: int = 0
        defibrillator: int = 0
        first_aid_kit: int = 0
    
    class Output(BaseModel):
        id: int
        user: User
        pistol: int = 0
        pistol_magnum: int = 0
        autoshotgun: int = 0
        shotgun_chrome: int = 0
        pumpshotgun: int = 0
        shotgun_spas: int = 0
        smg: int = 0
        smg_mp5: int = 0
        smg_silenced: int = 0
        rifle_ak47: int = 0
        rifle_sg552: int = 0
        rifle: int = 0
        rifle_m60: int = 0
        rifle_desert: int = 0
        hunting_rifle: int = 0
        sniper_military: int = 0
        sniper_awp: int = 0
        sniper_scout: int = 0
        weapon_grenade_launcher: int = 0
        molotov: int = 0
        pipe_bomb: int = 0
        vomitjar: int = 0
        melee: int = 0
        baseball_bat: int = 0
        cricket_bat: int = 0
        crowbar: int = 0
        electric_guitar: int = 0
        fireaxe: int = 0
        frying_pan: int = 0
        katana: int = 0
        knife: int = 0
        machete: int = 0
        tonfa: int = 0
        pain_pills: int = 0
        adrenaline: int = 0
        defibrillator: int = 0
        first_aid_kit: int = 0

class SteamVerifyRequest(BaseModel):
    steamid: str
    personaname: str
    avatar: str
    avatarfull: Optional[str] = None
    profileurl: str

class SteamVerifyResponse(BaseModel):
    access_token: str
    user: User
    steamInfo: PlayerSummary
    privileges: PrivilegesList

class AuthMeResponse(BaseModel):
    user: User
    steamInfo: PlayerSummary
    privileges: PrivilegesList