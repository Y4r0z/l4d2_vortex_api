from sqlalchemy import ForeignKey, String, Integer, Float, DateTime, Text, SmallInteger, Date, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column as column, relationship, sessionmaker
from sqlalchemy.sql import func as sqlFunc
from typing import List, Optional
import datetime
import os
from sqlalchemy import create_engine
from sqlalchemy import Index, event
from src.settings import SQL_CONNECT_STRING
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

#'2050-01-01T00:00:00'
BoostyPrivilegeUntil = datetime.datetime(year=2050, month=1, day=1, hour=0, minute=0, second=0)

engine = create_engine(SQL_CONNECT_STRING)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# asyncEngine = create_async_engine(SQL_CONNECT_STRING)
# AsyncSessionLocal = sessionmaker(asyncEngine, _class=AsyncSession, autoflush=False, autocommit=False) #type: ignore

class Base(DeclarativeBase):
    pass
class IDModel(Base):
    __abstract__ = True
    id : Mapped[int] = column(primary_key=True, autoincrement=True)

class User(IDModel):
    __tablename__ = "user"
    steamId : Mapped[str] = column(String(128))
    perks : Mapped[List["PerkSet"]] = relationship(back_populates='user')
    privileges : Mapped[List["PrivilegeStatus"]] = relationship(back_populates='user')
    tokens : Mapped[List["AuthToken"]] = relationship(back_populates='user')
    welcomePhrases : Mapped[List["WelcomePhrase"]] = relationship(back_populates='user')
    customPrefixes : Mapped[List["CustomPrefix"]] = relationship(back_populates='user')
    balance : Mapped["Balance"] = relationship(back_populates='user')
    discordLink : Mapped["SteamDiscordLink"] = relationship(back_populates='user')
    music: Mapped["PlayerMusic"] = relationship(back_populates='user', uselist=False)
    volume: Mapped["PlayerVolume"] = relationship(back_populates='user', uselist=False)



class ServerStatus(IDModel):
    __tablename__ = "server_status"
    name: Mapped[str] = column(String(128))
    ip: Mapped[str] = column(String(64))
    port: Mapped[int] = column(Integer)
    map: Mapped[str] = column(String(64))
    mode: Mapped[str] = column(String(32), default="default")
    max_slots: Mapped[int] = column(Integer, default=8)
    current_players: Mapped[int] = column(Integer, default=0)
    last_update: Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now(), onupdate=sqlFunc.now())
    players: Mapped[List["ServerPlayer"]] = relationship(back_populates='server', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_server_ip_port', 'ip', 'port', unique=True),
    )

class ServerPlayer(IDModel):
    __tablename__ = "server_player"
    server_id: Mapped[int] = column(ForeignKey('server_status.id', ondelete='CASCADE'))
    server: Mapped["ServerStatus"] = relationship(back_populates='players')
    user_id: Mapped[int] = column(Integer)
    steam_id: Mapped[str] = column(String(64))
    name: Mapped[str] = column(String(128))
    ip: Mapped[str] = column(String(64))
    connection_time: Mapped[float] = column(Float, default=0)
    last_update: Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now(), onupdate=sqlFunc.now())
    
    __table_args__ = (
        Index('idx_server_player_steamid', 'steam_id'),
        Index('idx_server_player_server', 'server_id'),
        Index('idx_server_player_unique', 'server_id', 'steam_id', unique=True),
    )



class PerkSet(IDModel):
    __tablename__ = "perkSet"
    survivorPerk1 : Mapped[str] = column(String(64))
    survivorPerk2 : Mapped[str] = column(String(64))
    survivorPerk3 : Mapped[str] = column(String(64))
    survivorPerk4 : Mapped[str] = column(String(64))

    boomerPerk : Mapped[str] = column(String(64))
    smokerPerk : Mapped[str] = column(String(64))
    hunterPerk : Mapped[str] = column(String(64))
    jockeyPerk : Mapped[str] = column(String(64))
    spitterPerk : Mapped[str] = column(String(64))
    chargerPerk : Mapped[str] = column(String(64))
    tankPerk : Mapped[str] = column(String(64))

    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())

    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='perks', cascade='all,delete')

#
# Access Levels:
#   0 - owner
#   1 - admin
#   2 - moderator
#   3 - jr. moderator
#   4 - other
class PrivilegeType(IDModel):
    __tablename__ = "privilegeType"
    accessLevel : Mapped[int] = column(Integer)
    name : Mapped[str] = column(String(64))
    description : Mapped[str] = column(String(512), default='')
    statuses : Mapped[List["PrivilegeStatus"]] = relationship(back_populates="privilege")


class PrivilegeStatus(IDModel):
    __tablename__ = "privilegeStatus"

    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='privileges', cascade='all,delete')

    privilegeId : Mapped[int] = column(ForeignKey('privilegeType.id'))
    privilege : Mapped["PrivilegeType"] = relationship(back_populates='statuses')

    activeUntil : Mapped[datetime.datetime] = column(DateTime(timezone=True), default=sqlFunc.now())

    __table_args__ = (
        Index('idx_privstatus_user_priv', 'userId', 'privilegeId'),
        Index('idx_privstatus_active', 'activeUntil'),
    )


class AuthToken(IDModel):
    __tablename__ = "authToken"
    token : Mapped[str] = column(String(256), nullable=False)
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='tokens')



class WelcomePhrase(IDModel):
    __tablename__ = "welcomePhrase"
    phrase : Mapped[str] = column(String(256), nullable=False)
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='welcomePhrases')


class CustomPrefix(IDModel):
    __tablename__ = "customPrefix"
    prefix : Mapped[str] = column(String(64), nullable=False)
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='customPrefixes')


class Balance(IDModel):
    __tablename__ = "balance"
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='balance')
    value : Mapped["int"] = column(Integer, default=0)
    transactions: Mapped[List["Transaction"]] = relationship(back_populates='balance')

class Transaction(IDModel):
    __tablename__ = "transaction"
    balanceId: Mapped[int] = column(ForeignKey('balance.id'))
    balance: Mapped["Balance"] = relationship(back_populates='transactions')
    value: Mapped[int] = column(Integer, default=0)
    description: Mapped[str] = column(String(128), default="none")
    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())

class DuplexTransaction(IDModel):
    __tablename__ = 'duplexTransaction'
    sourceId: Mapped[int] = column(ForeignKey('balance.id'))
    targetId: Mapped[int] = column(ForeignKey('balance.id'))
    source: Mapped["Balance"] = relationship('Balance', foreign_keys='DuplexTransaction.sourceId')
    target: Mapped["Balance"] = relationship('Balance', foreign_keys='DuplexTransaction.targetId')
    value: Mapped[int] = column(Integer, default=0)
    description: Mapped[str] = column(String(128), default="none")
    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())


class SteamDiscordLink(IDModel):
    __tablename__ = 'steamDiscordLink'
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='discordLink')
    discordId : Mapped[int] = column(String(64))

    __table_args__ = (
        Index('idx_discordlink_discordid', 'discordId'),
    )

class ChatLog(IDModel):
    __tablename__ = 'chatLogs'
    steamId : Mapped[str] = column(String(64))
    nickname: Mapped[str] = column(String(64), nullable=True, default=None)
    text: Mapped[str] = column(Text)
    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())
    server : Mapped[str] = column(String(32), default='None')
    team : Mapped[int] = column(SmallInteger, default=0)
    chatTeam : Mapped[int] = column(SmallInteger, default=0)

    __table_args__ = (
        Index('idx_chatlog_time', 'time'),
        Index('idx_chatlog_steamid', 'steamId'),
        Index('idx_chatlog_server', 'server'),
        Index('idx_chatlog_nickname', 'nickname'),
    )


class RoundScore(IDModel):
    __tablename__ = 'roundScore'
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship('User', foreign_keys='RoundScore.userId')
    agression: Mapped[int] = column(Integer, default=0)
    support: Mapped[int] = column(Integer, default=0)
    perks: Mapped[int] = column(Integer, default=0)
    team : Mapped[int] = column(SmallInteger, default=0)
    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())
    
    __table_args__ = (
        Index('idx_roundscore_userid', 'userId'),
        Index('idx_roundscore_scores', 'agression', 'support', 'perks'),
    )

class RoundScorePermanent(IDModel):
    __tablename__ = 'roundScore_Permanent'
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship('User', foreign_keys='RoundScorePermanent.userId')
    agression: Mapped[int] = column(Integer, default=0)
    support: Mapped[int] = column(Integer, default=0)
    perks: Mapped[int] = column(Integer, default=0)
    team : Mapped[int] = column(SmallInteger, default=0)
    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())

class ScoreSeason(IDModel):
    __tablename__ = 'scoreSeason'
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship('User', foreign_keys='ScoreSeason.userId')
    agression: Mapped[int] = column(Integer, default=0)
    support: Mapped[int] = column(Integer, default=0)
    perks: Mapped[int] = column(Integer, default=0)
    date: Mapped[datetime.date] = column(Date)


class PlaySession(IDModel):
    __tablename__ = 'playSession'
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship('User', foreign_keys='PlaySession.userId')
    timeFrom : Mapped[datetime.datetime] = column(DateTime(timezone=True))
    timeTo : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())
    
    __table_args__ = (
        Index('idx_playsession_userid', 'userId'),
    )

class MoneyDrop(IDModel):
    __tablename__ = 'moneyDrop'
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship('User', foreign_keys='MoneyDrop.userId')
    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())
    value: Mapped[int] = column(Integer, default=0)

class Giveaway(IDModel):
    __tablename__ = 'giveaway'
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship('User', foreign_keys='Giveaway.userId')
    timeCreated : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())
    activeUntil : Mapped[datetime.datetime] = column(DateTime(timezone=True))
    maxUseCount: Mapped[int] = column(Integer, default=1)
    curUseCount: Mapped[int] = column(Integer, default=0)
    reward: Mapped[int] = column(Integer)
class GiveawayUse(IDModel):
    __tablename__ = 'giveawayUse'
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship('User', foreign_keys='GiveawayUse.userId')
    giveawayId : Mapped[int] = column(ForeignKey('giveaway.id', ondelete='cascade'))
    giveaway : Mapped["Giveaway"] = relationship('Giveaway', foreign_keys='GiveawayUse.giveawayId', cascade='all,delete')
    time: Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())



class L4D2Item(IDModel):
    __tablename__ = 'l4d2Item'
    name: Mapped[str] = column(String(64), default='L4D2 Item')
    command: Mapped[str] = column(String(128))

class PrivilegeItem(IDModel):
    __tablename__ = 'privilegeItem'
    name: Mapped[str] = column(String(64), default='Privilege Item')
    privilegeTypeId: Mapped[int] = column(ForeignKey('privilegeType.id', ondelete='cascade'))
    privilegeType: Mapped["PrivilegeType"] = relationship('PrivilegeType', foreign_keys='PrivilegeItem.privilegeTypeId')
    duration: Mapped[int] = column(Integer)

class Reward(IDModel):
    __tablename__ = 'reward'
    name: Mapped[str] = column(String(64), default='Reward')
    itemId: Mapped[int] = column(ForeignKey('l4d2Item.id', ondelete='cascade'), nullable=True, default=None)
    item: Mapped["L4D2Item"] = relationship('L4D2Item', foreign_keys='Reward.itemId')
    privilegeItemId: Mapped[int] = column(ForeignKey('privilegeItem.id', ondelete='cascade'), nullable=True, default=None)
    privilegeItem: Mapped["PrivilegeItem"] = relationship('PrivilegeItem', foreign_keys='Reward.privilegeItemId')
    dailyQuests: Mapped[List["DailyQuest"]] = relationship('DailyQuest', secondary='dailyQuests_Rewards', back_populates='rewards')

class SimpleQuest(IDModel):
    __tablename__ = 'simpleQuest'
    name: Mapped[str] = column(String(64), default='Simple Quest')
    description: Mapped[str] = column(String(128), default='This is a simple quest')
    rewardId: Mapped[int] = column(ForeignKey('reward.id', ondelete='cascade'))
    reward: Mapped["Reward"] = relationship('Reward', foreign_keys='SimpleQuest.rewardId')
    
class DailyQuest(IDModel):
    __tablename__ = 'dailyQuest'
    activeUntil: Mapped[datetime.datetime] = column(DateTime(timezone=True))
    curProgress: Mapped[int] = column(Integer, default=0)
    maxProgress: Mapped[int] = column(Integer, default=1)
    questId: Mapped[int] = column(ForeignKey('simpleQuest.id', ondelete='cascade'))
    userId: Mapped[int] = column(ForeignKey('user.id', ondelete='cascade'))
    user: Mapped["User"] = relationship('User', foreign_keys='DailyQuest.userId')
    rewards: Mapped[List["Reward"]] = relationship('Reward', secondary='dailyQuests_Rewards', back_populates='dailyQuests')

class DailyQuests_Rewards(IDModel):
    __tablename__ = 'dailyQuests_Rewards'
    dailyQuestId: Mapped[int] = column(ForeignKey('dailyQuest.id', ondelete='cascade'))
    rewardId: Mapped[int] = column(ForeignKey('reward.id', ondelete='cascade'))

class EmptyDrop(IDModel):
    __tablename__ = 'emptyDrop'
    userId: Mapped[int] = column(ForeignKey('user.id', ondelete='cascade'))
    user: Mapped["User"] = relationship('User', foreign_keys='EmptyDrop.userId')
    time: Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())



class UserInventory(IDModel):
    __tablename__ = 'userInventory'
    userId: Mapped[int] = column(ForeignKey('user.id', ondelete='cascade'))
    user: Mapped["User"] = relationship('User', foreign_keys='UserInventory.userId')
    itemId: Mapped[int] = column(ForeignKey('l4d2Item.id', ondelete='cascade'))
    item: Mapped["L4D2Item"] = relationship('L4D2Item', foreign_keys='UserInventory.itemId')
    activeUntil: Mapped[datetime.datetime] = column(DateTime(timezone=True))

    

    
class PlayerMusic(IDModel):
    __tablename__ = "player_music"
    
    soundname: Mapped[str] = column(String(255), nullable=False)
    userId: Mapped[int] = column(ForeignKey('user.id', ondelete='cascade'))
    nick: Mapped[str] = column(String(128), nullable=True)
    path: Mapped[str] = column(String(255), nullable=False)
    url: Mapped[str] = column(String(255), nullable=True)
    playcount: Mapped[int] = column(Integer, default=0)
    updated_at: Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now(), onupdate=sqlFunc.now())
    
    user: Mapped["User"] = relationship(back_populates='music')

class PlayerVolume(IDModel):
    __tablename__ = "player_volume"
    
    volume: Mapped[int] = column(Integer, default=50)
    updated_at: Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now(), onupdate=sqlFunc.now())
    
    userId: Mapped[int] = column(ForeignKey('user.id', ondelete='cascade'))
    user: Mapped["User"] = relationship(back_populates='volume')

class PlayerSound(IDModel):
    __tablename__ = "player_sounds"
    
    soundname: Mapped[str] = column(String(255), nullable=False)
    path: Mapped[str] = column(String(255), nullable=False)
    cooldown: Mapped[float] = column(Float, nullable=False)
    playcount: Mapped[int] = column(Integer, default=0)

class StPlayerBase(IDModel):
    __tablename__ = 'st_player_base'
    userId: Mapped[int] = column(ForeignKey('user.id', ondelete='cascade'))
    user: Mapped["User"] = relationship('User', foreign_keys='StPlayerBase.userId')
    last_nickname: Mapped[str] = column(String(128), nullable=True)
    last_online: Mapped[str] = column(String(32), nullable=True)
    last_ip: Mapped[str] = column(String(64), nullable=True)
    last_country: Mapped[str] = column(String(64), nullable=True)
    last_city: Mapped[str] = column(String(64), nullable=True)
    last_region: Mapped[str] = column(String(64), nullable=True)
    
    __table_args__ = (
        Index('idx_st_player_base_userid', 'userId', unique=True),
    )

class StPlayerHits(IDModel):
    __tablename__ = 'st_player_hits'
    userId: Mapped[int] = column(ForeignKey('user.id', ondelete='cascade'))
    user: Mapped["User"] = relationship('User', foreign_keys='StPlayerHits.userId')
    NULL_HITBOX: Mapped[int] = column(Integer, default=0)
    HEAD: Mapped[int] = column(Integer, default=0)
    CHEST: Mapped[int] = column(Integer, default=0)
    STOMACH: Mapped[int] = column(Integer, default=0)
    LEFT_ARM: Mapped[int] = column(Integer, default=0)
    RIGHT_ARM: Mapped[int] = column(Integer, default=0)
    LEFT_LEG: Mapped[int] = column(Integer, default=0)
    RIGHT_LEG: Mapped[int] = column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_st_player_hits_userid', 'userId', unique=True),
    )

class StPlayerKills(IDModel):
    __tablename__ = 'st_player_kills'
    userId: Mapped[int] = column(ForeignKey('user.id', ondelete='cascade'))
    user: Mapped["User"] = relationship('User', foreign_keys='StPlayerKills.userId')
    survivor_killed: Mapped[int] = column(Integer, default=0)
    infected_killed: Mapped[int] = column(Integer, default=0)
    smoker_killed: Mapped[int] = column(Integer, default=0)
    boomer_killed: Mapped[int] = column(Integer, default=0)
    hunter_killed: Mapped[int] = column(Integer, default=0)
    spitter_killed: Mapped[int] = column(Integer, default=0)
    jockey_killed: Mapped[int] = column(Integer, default=0)
    charger_killed: Mapped[int] = column(Integer, default=0)
    witch_killed: Mapped[int] = column(Integer, default=0)
    tank_killed: Mapped[int] = column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_st_player_kills_userid', 'userId', unique=True),
    )

class StPlayerShots(IDModel):
    __tablename__ = 'st_player_shots'
    userId: Mapped[int] = column(ForeignKey('user.id', ondelete='cascade'))
    user: Mapped["User"] = relationship('User', foreign_keys='StPlayerShots.userId')
    player_death: Mapped[int] = column(Integer, default=0)
    player_fire: Mapped[int] = column(Integer, default=0)
    player_hits: Mapped[int] = column(Integer, default=0)
    player_heads: Mapped[int] = column(Integer, default=0)
    player_damage: Mapped[int] = column(Integer, default=0)
    player_hurt: Mapped[int] = column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_st_player_shots_userid', 'userId', unique=True),
    )

class StPlayerWeapon(IDModel):
    __tablename__ = 'st_player_weapon'
    userId: Mapped[int] = column(ForeignKey('user.id', ondelete='cascade'))
    user: Mapped["User"] = relationship('User', foreign_keys='StPlayerWeapon.userId')
    pistol: Mapped[int] = column(Integer, default=0)
    pistol_magnum: Mapped[int] = column(Integer, default=0)
    autoshotgun: Mapped[int] = column(Integer, default=0)
    shotgun_chrome: Mapped[int] = column(Integer, default=0)
    pumpshotgun: Mapped[int] = column(Integer, default=0)
    shotgun_spas: Mapped[int] = column(Integer, default=0)
    smg: Mapped[int] = column(Integer, default=0)
    smg_mp5: Mapped[int] = column(Integer, default=0)
    smg_silenced: Mapped[int] = column(Integer, default=0)
    rifle_ak47: Mapped[int] = column(Integer, default=0)
    rifle_sg552: Mapped[int] = column(Integer, default=0)
    rifle: Mapped[int] = column(Integer, default=0)
    rifle_m60: Mapped[int] = column(Integer, default=0)
    rifle_desert: Mapped[int] = column(Integer, default=0)
    hunting_rifle: Mapped[int] = column(Integer, default=0)
    sniper_military: Mapped[int] = column(Integer, default=0)
    sniper_awp: Mapped[int] = column(Integer, default=0)
    sniper_scout: Mapped[int] = column(Integer, default=0)
    weapon_grenade_launcher: Mapped[int] = column(Integer, default=0)
    molotov: Mapped[int] = column(Integer, default=0)
    pipe_bomb: Mapped[int] = column(Integer, default=0)
    vomitjar: Mapped[int] = column(Integer, default=0)
    melee: Mapped[int] = column(Integer, default=0)
    baseball_bat: Mapped[int] = column(Integer, default=0)
    cricket_bat: Mapped[int] = column(Integer, default=0)
    crowbar: Mapped[int] = column(Integer, default=0)
    electric_guitar: Mapped[int] = column(Integer, default=0)
    fireaxe: Mapped[int] = column(Integer, default=0)
    frying_pan: Mapped[int] = column(Integer, default=0)
    katana: Mapped[int] = column(Integer, default=0)
    knife: Mapped[int] = column(Integer, default=0)
    machete: Mapped[int] = column(Integer, default=0)
    tonfa: Mapped[int] = column(Integer, default=0)
    pain_pills: Mapped[int] = column(Integer, default=0)
    adrenaline: Mapped[int] = column(Integer, default=0)
    defibrillator: Mapped[int] = column(Integer, default=0)
    first_aid_kit: Mapped[int] = column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_st_player_weapon_userid', 'userId', unique=True),
    )