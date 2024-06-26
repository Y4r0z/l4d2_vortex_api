from sqlalchemy import ForeignKey, String, Integer, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column as column, relationship, sessionmaker
from sqlalchemy.sql import func as sqlFunc
from typing import List, Optional
import datetime
import os
from sqlalchemy import create_engine


engine = create_engine(os.environ.get("SQL_CONNECT_STRING"))
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



    