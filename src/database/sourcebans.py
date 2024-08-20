from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine
import src.settings as settings

from sqlalchemy.sql.schema import Column, Index, Table
from sqlalchemy.sql.sqltypes import Integer, SmallInteger, String, Text
from sqlalchemy.schema import FetchedValue


sb_engine = create_async_engine(settings.SOURCEBANS_CONNECT_STRING)
sb_session = async_sessionmaker(sb_engine)

sb_engine_sync = create_engine(settings.SOURCEBANS_CONNECT_STRING.replace('aiomysql', 'pymysql'))
sb_session_sync = sessionmaker(sb_engine_sync)

async def getSourcebans():
    async with sb_session() as session:
        yield session
        
def getSourcebansSync():
    with sb_session_sync() as session:
        yield session

class SbBase(DeclarativeBase):
    __abstract__ = True


# Все эти модели работют конкретно с нашей версией SB, если у вас другая, делайте свои

class SbServer(SbBase):
    __tablename__ = 'sb_servers'
    __table_args__ = (
        Index('ip', 'ip', 'port'),
    )

    sid = Column(Integer, primary_key=True)
    ip = Column(String(64), nullable=False)
    port = Column(Integer, nullable=False)
    rcon = Column(String(64), nullable=False)
    modid = Column(Integer, nullable=False)
    enabled = Column(Integer, nullable=False, server_default=FetchedValue())


class SbBan(SbBase):
    __tablename__ = 'sb_bans'
    __table_args__ = (
        Index('type_ip', 'type', 'ip'),
        Index('type_authid', 'type', 'authid')
    )

    bid = Column(Integer, primary_key=True)
    ip = Column(String(32))
    authid = Column(String(64), nullable=False, index=True, server_default=FetchedValue())
    name = Column(String(128), nullable=False, server_default=FetchedValue())
    created = Column(Integer, nullable=False, server_default=FetchedValue())
    ends = Column(Integer, nullable=False, server_default=FetchedValue())
    length = Column(Integer, nullable=False, server_default=FetchedValue())
    reason = Column(Text, nullable=False, index=True)
    aid = Column(Integer, nullable=False, server_default=FetchedValue())
    adminIp = Column(String(32), nullable=False, server_default=FetchedValue())
    sid = Column(Integer, nullable=False, index=True, server_default=FetchedValue())
    country = Column(String(4))
    RemovedBy = Column(Integer)
    RemoveType = Column(String(3))
    RemovedOn = Column(Integer)
    type = Column(Integer, nullable=False, server_default=FetchedValue())
    ureason = Column(Text)
