from sqlalchemy.orm import Session
from sqlalchemy import and_, func, select
import src.database.models as Models
import src.types.api_models as Schemas
import src.database.predefined as Predefined
import datetime
from typing import List

def get_user(db: Session, steam_id: str):
    return db.query(Models.User).filter(Models.User.steamId == steam_id).first()

def create_user(db: Session, steam_id: str) -> Models.User:
    user = Models.User(steamId=steam_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_perks(db: Session, user_id: int) -> Models.PerkSet | None:
    return db.query(Models.PerkSet).filter(Models.PerkSet.userId == user_id).order_by(Models.PerkSet.time.desc()).first()

def set_perks(db:Session, user_id: int, perks: Schemas.PerkSet) -> Models.PerkSet:
    perkSet = Models.PerkSet(
        **perks.model_dump(),
        userId = user_id
    )
    db.add(perkSet)
    db.commit()
    db.refresh(perkSet)
    return perkSet

def check_token(db: Session, token: str, accessLevel:int = 0):
    found = db.query(Models.AuthToken).filter(Models.AuthToken.token == token).first()
    return found is not None

def __checkPriv(db: Session, user_id: int, priv_id: int):
    prv = db.query(Models.PrivilegeStatus)\
        .filter(Models.PrivilegeStatus.privilegeId == priv_id, Models.PrivilegeStatus.userId == user_id)\
        .order_by(Models.PrivilegeStatus.activeUntil.desc()).first()
    if prv is None: return False
    return prv.activeUntil > datetime.datetime.now()

def get_privileges(db: Session, user_id: int) -> Schemas.PrivilegesList:
    prv = Schemas.PrivilegesList()
    prv.owner = __checkPriv(db, user_id, Predefined.PrivilegeTypes['owner'].id)
    prv.admin = __checkPriv(db, user_id, Predefined.PrivilegeTypes['admin'].id)
    prv.moderator = __checkPriv(db, user_id, Predefined.PrivilegeTypes['moderator'].id)
    prv.soundpad = __checkPriv(db, user_id, Predefined.PrivilegeTypes['soundpad'].id)
    prv.mediaPlayer = __checkPriv(db, user_id, Predefined.PrivilegeTypes['media_player'].id)
    prv.vip = __checkPriv(db, user_id, Predefined.PrivilegeTypes['vip'].id)
    prv.premium = __checkPriv(db, user_id, Predefined.PrivilegeTypes['premium'].id)
    prv.legend = __checkPriv(db, user_id, Predefined.PrivilegeTypes['legend'].id)
    phrase = db.query(Models.WelcomePhrase).filter(Models.WelcomePhrase.userId == user_id).first()
    wp = __checkPriv(db, user_id, Predefined.PrivilegeTypes['welcomePhrase'].id) \
        or __checkPriv(db, user_id, Predefined.PrivilegeTypes['legend'].id)
    prv.welcomePhrase = phrase.phrase if wp and phrase is not None else ""
    prefix = db.query(Models.CustomPrefix).filter(Models.CustomPrefix.userId == user_id).first()
    prv.customPrefix = prefix.prefix if __checkPriv(db, user_id, Predefined.PrivilegeTypes['customPrefix'].id) and prefix is not None else ""
    prv.discord = db.query(Models.SteamDiscordLink).filter(Models.SteamDiscordLink.userId == user_id).first() is not None
    return prv

def add_privilege(db: Session, user_id: int, priv_id: int, until: datetime.datetime) -> Models.PrivilegeStatus:
    priv = Models.PrivilegeStatus(userId=user_id, privilegeId=priv_id, activeUntil=until)
    db.add(priv)
    db.commit()
    db.refresh(priv)
    return priv

def get_privilegeType(db: Session, priv_id: int) -> Models.PrivilegeType | None:
    priv = db.query(Models.PrivilegeType).filter(Models.PrivilegeType.id == priv_id).first()
    return priv

def get_privilegeTypes(db: Session) -> List[Models.PrivilegeType]:
    priv = db.query(Models.PrivilegeType).all()
    return priv

def get_privilegeStatus(db: Session, privStatus_id: int):
    privStatus = db.query(Models.PrivilegeStatus).filter(Models.PrivilegeStatus.id == privStatus_id).first()
    return privStatus

def get_privilegeStatuses(db: Session, user_id: int) -> List[Models.PrivilegeStatus]:
    privs = db.query(Models.PrivilegeStatus).filter(Models.PrivilegeStatus.userId == user_id).all()
    return privs

def delete_privilegeStatus(db: Session, priv_id: int):
    db.query(Models.PrivilegeStatus).filter(Models.PrivilegeStatus.id == priv_id).delete()
    db.commit()

def edit_privilegeStatus(db: Session, privStatus_id: int, priv_id: int, until: datetime.datetime) -> Models.PrivilegeStatus | None:
    priv = db.query(Models.PrivilegeStatus).filter(Models.PrivilegeStatus.id == privStatus_id).first()
    if priv is None: return None
    priv.privilegeId = priv_id
    priv.activeUntil = until
    db.commit()
    db.refresh(priv)
    return priv


def set_welcomePhrase(db: Session, user_id: int, phrase: str) -> Models.WelcomePhrase:
    obj = db.query(Models.WelcomePhrase).filter(Models.WelcomePhrase.userId == user_id).first()
    if obj is None:
        obj = Models.WelcomePhrase(userId = user_id, phrase = phrase)
        db.add(obj)
    else:
        obj.phrase = phrase
    db.commit()
    db.refresh(obj)
    return obj

def set_customPrefix(db: Session, user_id: int, prefix: str) -> Models.CustomPrefix:
    obj = db.query(Models.CustomPrefix).filter(Models.CustomPrefix.userId == user_id).first()
    if obj is None:
        obj = Models.CustomPrefix(userId = user_id, prefix = prefix)
        db.add(obj)
    else:
        obj.prefix = prefix
    db.commit()
    db.refresh(obj)
    return obj

def find_users(db: Session, query: str) -> List[Models.User]:
    users = db.query(Models.User).filter(Models.User.steamId.like(f'%{query}%')).limit(10).all()
    return users

def find_discord(db: Session, query: str) -> List[Models.SteamDiscordLink]:
    links = db.query(Models.SteamDiscordLink).filter(Models.SteamDiscordLink.discordId.like(f'%{query}%')).limit(10).all()
    return links

def get_discord(db: Session, discord_id: str) -> Models.SteamDiscordLink | None:
    link = db.query(Models.SteamDiscordLink).filter(Models.SteamDiscordLink.discordId == discord_id).first()
    return link

def create_discord(db: Session, user : Models.User, discord_id: str) -> Models.SteamDiscordLink:
    existing = db.query(Models.SteamDiscordLink).filter(Models.SteamDiscordLink.discordId == discord_id).first()
    if existing:
        db.delete(existing)
        
    link = Models.SteamDiscordLink(discordId=discord_id, userId=user.id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

def delete_discord(db: Session, discord_id: str):
    link = get_discord(db, discord_id)
    if link is None: return
    db.delete(link)
    db.commit()

def get_discord_steam(db: Session, user: Models.User) -> Models.SteamDiscordLink | None:
    link = db.query(Models.SteamDiscordLink).filter(Models.SteamDiscordLink.userId == user.id).first()
    return link


def create_logs(db: Session, logs: List[Schemas.ChatLog]):
    """
    Создает новые записи логов чата с обработкой ошибок
    """
    try:
        chat_logs = [
            Models.ChatLog(
                steamId=log.steamId, 
                nickname=log.nickname, 
                text=log.text, 
                time=log.time, 
                server=log.server, 
                team=log.team, 
                chatTeam=log.chatTeam
            ) 
            for log in logs
        ]
        db.bulk_save_objects(chat_logs)
        db.commit()
    except Exception as e:
        db.rollback()
        raise

def get_logs(db: Session, text: str, steam_id: str, nick: str | None, server: str, offset: int, count: int, start_time: datetime.datetime, end_time: datetime.datetime) -> List[Models.ChatLog]:
    """
    Получает логи чата с оптимизированными запросами
    """
    try:
        count = min(count, 100)
        
        query = db.query(Models.ChatLog).filter(
            Models.ChatLog.time.between(start_time, end_time)
        )
        
        if steam_id:
            query = query.filter(Models.ChatLog.steamId.like(f'%{steam_id}%'))
        
        if nick is not None:
            query = query.filter(Models.ChatLog.nickname.like(f'%{nick}%'))
        
        if text:
            query = query.filter(Models.ChatLog.text.like(f'%{text}%'))
        
        if server:
            query = query.filter(Models.ChatLog.server.like(f'%{server}%'))
            
        # Сортируем и применяем пагинацию
        return query.order_by(Models.ChatLog.time.desc()).offset(offset).limit(count).all()
    except Exception as e:
        raise


def get_player_rank(db: Session, user: Models.User) -> tuple[int] | None:
    subquery = select(
        Models.RoundScore.userId, 
        func.dense_rank().over(order_by=func.sum(Models.RoundScore.agression + Models.RoundScore.support + Models.RoundScore.perks).desc()).label('rank')
    ).group_by(Models.RoundScore.userId).alias('tbl')
    query = select(subquery.c.rank).where(subquery.c.userId == user.id)
    result = db.execute(query).first()
    if result is None: return None
    return result.tuple()[0]

def get_player_rank_score(db: Session, user: Models.User) -> tuple[int, int] | None:
    subquery = select(
        Models.RoundScore.userId, 
        func.sum(Models.RoundScore.agression + Models.RoundScore.support + Models.RoundScore.perks).label('score'),
        func.dense_rank().over(order_by=func.sum(Models.RoundScore.agression + Models.RoundScore.support + Models.RoundScore.perks).desc()).label('rank')
    ).group_by(Models.RoundScore.userId).alias('tbl')
    query = select(subquery.c.rank, subquery.c.score).where(subquery.c.userId == user.id)
    result = db.execute(query).first()
    if result is None: return None
    return result.tuple()

def get_player_music(db: Session, user_id: int) -> Models.PlayerMusic | None:
    return db.query(Models.PlayerMusic).filter(Models.PlayerMusic.userId == user_id).first()

def set_player_music(db: Session, user_id: int, music_data: Schemas.PlayerMusic.Input) -> Models.PlayerMusic:
    music = db.query(Models.PlayerMusic).filter(Models.PlayerMusic.userId == user_id).first()
    if music:
        music.soundname = music_data.soundname
        music.path = music_data.path
        if music_data.url is not None:
            music.url = music_data.url
        if music_data.nick is not None:
            music.nick = music_data.nick
    else:
        music = Models.PlayerMusic(
            userId=user_id,
            **music_data.model_dump()
        )
        db.add(music)
    db.commit()
    db.refresh(music)
    return music

def increment_playcount_by_steam(db: Session, user_id: int) -> Models.PlayerMusic:
    music = db.query(Models.PlayerMusic).filter(Models.PlayerMusic.userId == user_id).first()
    if music:
        music.playcount += 1
        db.commit()
        db.refresh(music)
    return music

def get_top_music(db: Session, limit: int = 10) -> List[Models.PlayerMusic]:
    return db.query(Models.PlayerMusic)\
             .order_by(Models.PlayerMusic.playcount.desc())\
             .limit(limit)\
             .all()

def get_all_music(
    db: Session, 
    offset: int = 0, 
    limit: int = 100,
    search: str | None = None
) -> List[Models.PlayerMusic]:
    query = db.query(Models.PlayerMusic)
    
    if search:
        query = query.filter(Models.PlayerMusic.soundname.ilike(f"%{search}%"))
    
    return query\
        .order_by(Models.PlayerMusic.updated_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()

def delete_player_music(db: Session, user_id: int) -> bool:
    music = db.query(Models.PlayerMusic).filter(Models.PlayerMusic.userId == user_id).first()
    if music:
        db.delete(music)
        db.commit()
        return True
    return False

def get_player_volume(db: Session, user_id: int) -> Models.PlayerVolume | None:
    return db.query(Models.PlayerVolume).filter(Models.PlayerVolume.userId == user_id).first()

def set_player_volume(db: Session, user_id: int, volume_data: Schemas.PlayerVolume.Input) -> Models.PlayerVolume:
    volume = db.query(Models.PlayerVolume).filter(Models.PlayerVolume.userId == user_id).first()
    
    validated_volume = max(0, min(volume_data.volume, 100))
    
    if volume:
        volume.volume = validated_volume
    else:
        volume = Models.PlayerVolume(
            userId=user_id,
            volume=validated_volume
        )
        db.add(volume)
    
    db.commit()
    db.refresh(volume)
    return volume