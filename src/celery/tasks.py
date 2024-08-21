from celery import Celery # type: ignore
import src.settings as settings
from sqlalchemy import select
from src.api.tools import get_db
from src.database.sourcebans import getSourcebansSync, SbServer
from src.database.models import ServerStats
from src.lib.rcon_api import getRconPlayers
from src.lib.source_query import getServerInfo, getServerPlayers
import datetime
import redis
import logging
import json

celery = Celery(__name__)
celery.conf.broker_url = settings.CELERY_BROKER_URL
celery.conf.result_backend = settings.CELERY_RESULT_BACKEND

redis_pool = redis.ConnectionPool.from_url(settings.REDIS_CONNECT_STRING, db=1)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    sender.add_periodic_task(60.0, fetch_server_info.s(), name='fetch_servers')




@celery.task
def print_test():
    with redis.Redis(connection_pool=redis_pool) as r:
        r.set('celery_test', datetime.datetime.now().isoformat())
    logging.info('Redis SET TEST LOG')

@celery.task
def fetch_server_info():
    logging.info('Fetching servers')
    db = next(get_db())
    sb = next(getSourcebansSync())
    
    serversQuery = select(SbServer).where(SbServer.enabled == 1)
    servers = [s._tuple()[0] for s in sb.execute(serversQuery).all()]
    for server in servers:
        players = []
        a2sPlayers = getServerPlayers(server)
        try:
            serverInfo = getServerInfo(server)
        except:
            logging.info("Failed to get server info")
            continue
        try:
            for p in getRconPlayers(server):
                try:
                    tt = next(p2 for p2 in a2sPlayers if p2.name == p.name).duration
                except Exception as e:
                    logging.info(f"Failed to get player duration: {str(e)}")
                    tt = 0
                players.append({
                    'id': p.id,
                    'ip': p.ip,
                    'name': p.name,
                    'time': tt,
                    'steamId': p.steam64id
                })
        except Exception as e:
            logging.info("Failed to get players")
        finalServer = {
            'id': server.sid,
            'name': serverInfo.server_name,
            'map': serverInfo.map_name,
            'playersCount': serverInfo.player_count,
            'maxPlayersCount': serverInfo.max_players,
            'ip': server.ip,
            'port': server.port,
            'ping': serverInfo.ping,
            'time': datetime.datetime.now().isoformat(),
            'keywords': serverInfo.keywords,
            'players': players
        }
        with redis.Redis(connection_pool=redis_pool) as r:
            r.set(f'server_info:{server.sid}', json.dumps(finalServer), ex=86400)
        serverObj = ServerStats(
            players=serverInfo.player_count,
            maxPlayers=serverInfo.max_players,
            map=serverInfo.map_name,
            name=serverInfo.server_name,
            ping=serverInfo.ping,
            ip=server.ip,
            port=server.port,
            sid=server.sid
        )
        db.add(serverObj)
    db.commit()
    logging.info('Servers fetched')
            