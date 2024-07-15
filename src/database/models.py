from sqlalchemy import ForeignKey, String, Integer, Float, DateTime, Text, SmallInteger
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


class User(Base):
    __tablename__ = "user"
    id : Mapped[int] = column(primary_key=True, autoincrement=True)
    steamId : Mapped[str] = column(String(128))
    perks : Mapped[List["PerkSet"]] = relationship(back_populates='user')
    privileges : Mapped[List["PrivilegeStatus"]] = relationship(back_populates='user')
    tokens : Mapped[List["AuthToken"]] = relationship(back_populates='user')
    welcomePhrases : Mapped[List["WelcomePhrase"]] = relationship(back_populates='user')
    customPrefixes : Mapped[List["CustomPrefix"]] = relationship(back_populates='user')
    balance : Mapped["Balance"] = relationship(back_populates='user')
    discordLink : Mapped["SteamDiscordLink"] = relationship(back_populates='user')


class PerkSet(Base):
    __tablename__ = "perkSet"
    id : Mapped[int] = column(primary_key=True, autoincrement=True)

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
class PrivilegeType(Base):
    __tablename__ = "privilegeType"
    id : Mapped[int] = column(primary_key=True, autoincrement=True)
    accessLevel : Mapped[int] = column(Integer)
    name : Mapped[str] = column(String(64))
    description : Mapped[str] = column(String(512), default='')
    statuses : Mapped[List["PrivilegeStatus"]] = relationship(back_populates="privilege")


class PrivilegeStatus(Base):
    __tablename__ = "privilegeStatus"
    id : Mapped[int] = column(primary_key=True, autoincrement=True)

    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='privileges', cascade='all,delete')

    privilegeId : Mapped[int] = column(ForeignKey('privilegeType.id'))
    privilege : Mapped["PrivilegeType"] = relationship(back_populates='statuses')

    activeUntil : Mapped[datetime.datetime] = column(DateTime(timezone=True), default=sqlFunc.now())


class AuthToken(Base):
    __tablename__ = "authToken"
    id : Mapped[int] = column(primary_key=True, autoincrement=True)
    token : Mapped[str] = column(String(256), nullable=False)
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='tokens')



class WelcomePhrase(Base):
    __tablename__ = "welcomePhrase"
    id : Mapped[int] = column(primary_key=True, autoincrement=True)
    phrase : Mapped[str] = column(String(256), nullable=False)
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='welcomePhrases')


class CustomPrefix(Base):
    __tablename__ = "customPrefix"
    id : Mapped[int] = column(primary_key=True, autoincrement=True)
    prefix : Mapped[str] = column(String(64), nullable=False)
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='customPrefixes')


class Balance(Base):
    __tablename__ = "balance"
    id : Mapped[int] = column(primary_key=True, autoincrement=True)
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='balance')
    value : Mapped["int"] = column(Integer, default=0)
    transactions: Mapped[List["Transaction"]] = relationship(back_populates='balance')

class Transaction(Base):
    __tablename__ = "transaction"
    id : Mapped[int] = column(primary_key=True, autoincrement=True)
    balanceId: Mapped[int] = column(ForeignKey('balance.id'))
    balance: Mapped["Balance"] = relationship(back_populates='transactions')
    value: Mapped[int] = column(Integer, default=0)
    description: Mapped[str] = column(String(128), default="none")
    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())

class DuplexTransaction(Base):
    __tablename__ = 'duplexTransaction'
    id : Mapped[int] = column(primary_key=True, autoincrement=True)
    sourceId: Mapped[int] = column(ForeignKey('balance.id'))
    targetId: Mapped[int] = column(ForeignKey('balance.id'))
    source: Mapped["Balance"] = relationship('Balance', foreign_keys='DuplexTransaction.sourceId')
    target: Mapped["Balance"] = relationship('Balance', foreign_keys='DuplexTransaction.targetId')
    value: Mapped[int] = column(Integer, default=0)
    description: Mapped[str] = column(String(128), default="none")
    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())


class SteamDiscordLink(Base):
    __tablename__ = 'steamDiscordLink'
    id : Mapped[int] = column(primary_key=True, autoincrement=True)
    userId : Mapped[int] = column(ForeignKey('user.id'))
    user : Mapped["User"] = relationship(back_populates='discordLink')
    discordId : Mapped[int] = column(String(64))

class ChatLog(Base):
    __tablename__ = 'chatLogs'
    id : Mapped[int] = column(primary_key=True, autoincrement=True)
    steamId : Mapped[str] = column(String(64))
    text: Mapped[str] = column(Text)
    time : Mapped[datetime.datetime] = column(DateTime(timezone=True), server_default=sqlFunc.now())
    server : Mapped[str] = column(String(32), default='None')
    team : Mapped[int] = column(SmallInteger, default=0)
    chatTeam : Mapped[int] = column(SmallInteger, default=0)
