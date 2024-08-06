from sqlalchemy import ForeignKey, String, Integer, Float, DateTime, Text, SmallInteger, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column as column, relationship, sessionmaker
from sqlalchemy.sql import func as sqlFunc
from typing import List, Optional
import datetime
import os
from sqlalchemy import create_engine


engine = create_engine(os.environ.get("SQL_CONNECT_STRING") or "")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

class ChatLog(IDModel):
    __tablename__ = 'chatLogs'
    steamId : Mapped[str] = column(String(64))
    nickname: Mapped[str] = column(String(64), nullable=True, default=None)
    text: Mapped[str] = column(Text)
    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())
    server : Mapped[str] = column(String(32), default='None')
    team : Mapped[int] = column(SmallInteger, default=0)
    chatTeam : Mapped[int] = column(SmallInteger, default=0)


class RoundScore(IDModel):
    __tablename__ = 'roundScore'
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship('User', foreign_keys='RoundScore.userId')
    agression: Mapped[int] = column(Integer, default=0)
    support: Mapped[int] = column(Integer, default=0)
    perks: Mapped[int] = column(Integer, default=0)
    team : Mapped[int] = column(SmallInteger, default=0)
    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())

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


