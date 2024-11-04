from celery import Celery
from celery.signals import worker_ready
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
import xml.etree.ElementTree as ET
import httpx

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация Celery
celery = Celery(__name__)
celery.conf.broker_url = settings.CELERY_BROKER_URL
celery.conf.result_backend = settings.CELERY_RESULT_BACKEND

# Добавляем конфигурации для повышения надежности
celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_timeout=10,
    result_extended=True,
    redis_max_connections=20
)

# Redis connection pool
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_CONNECT_STRING, 
    db=1,
    socket_timeout=5,
    socket_connect_timeout=5
)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    # Каждую минуту
    sender.add_periodic_task(60.0, fetch_server_info.s(), name='fetch_servers')
    # Каждые 30 минут
    sender.add_periodic_task(1800.0, parse_group.s(), name='parse_group')

@worker_ready.connect
def at_start(sender, **kwargs):
    with sender.app.connection() as conn:
        sender.app.send_task('src.celery.tasks.parse_group', connection=conn)

def process_single_server(server: SbServer, db):
    """
    Обработка информации для одного сервера
    """
    players = []
    
    # Получение информации о сервере
    try:
        serverInfo = getServerInfo(server, timeout=5)
    except Exception as e:
        logger.error(f"Failed to get server info for {server.ip}:{server.port}: {str(e)}", exc_info=True)
        return
    
    # Получение списка игроков через A2S
    try:
        a2sPlayers = getServerPlayers(server)
    except Exception as e:
        logger.error(f"Failed to get A2S players for {server.ip}:{server.port}: {str(e)}", exc_info=True)
        a2sPlayers = []

    # Получение списка игроков через RCON
    try:
        rcon_players = getRconPlayers(server)
        for p in rcon_players:
            try:
                # Поиск времени игрока из A2S данных
                tt = next((p2.duration for p2 in a2sPlayers if p2.name == p.name), 0)
            except Exception as e:
                logger.error(f"Failed to match player {p.name}: {str(e)}")
                tt = 0
            
            players.append({
                'id': p.id,
                'ip': p.ip,
                'name': p.name,
                'time': tt,
                'steamId': p.steam64id
            })
    except Exception as e:
        logger.error(f"Failed to get RCON players from {server.ip}:{server.port}: {str(e)}", exc_info=True)

    # Формирование финальных данных
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

    # Сохранение в Redis
    try:
        with redis.Redis(connection_pool=redis_pool) as r:
            r.set(f'server_info:{server.sid}', json.dumps(finalServer), ex=86400)
    except redis.RedisError as e:
        logger.error(f"Redis error while saving server {server.ip}:{server.port}: {str(e)}", exc_info=True)

    # Сохранение в базу данных
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

@celery.task(
    bind=True,
    max_retries=3,
    retry_backoff=True,
    soft_time_limit=300,  # 5 минут на выполнение
    time_limit=360,
    name="fetch_server_info"
)
def fetch_server_info(self):
    """
    Задача получения информации со всех серверов
    """
    logger.info('Starting server info fetch')
    db = None
    sb = None
    
    try:
        db = next(get_db())
        sb = next(getSourcebansSync())
        
        # Получение списка активных серверов
        serversQuery = select(SbServer).where(SbServer.enabled == 1)
        servers = [s._tuple()[0] for s in sb.execute(serversQuery).all()]
        
        # Обработка каждого сервера
        for server in servers:
            try:
                process_single_server(server, db)
            except Exception as e:
                logger.error(f"Error processing server {server.ip}:{server.port}: {str(e)}", exc_info=True)
                continue
                
        # Сохранение всех изменений в БД
        db.commit()
        logger.info('Servers fetch completed successfully')
        
    except Exception as exc:
        logger.error(f"Critical error in fetch_server_info: {str(exc)}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)
    finally:
        # Закрытие соединений
        if db is not None:
            db.close()
        if sb is not None:
            sb.close()

@celery.task(
    bind=True,
    max_retries=3,
    retry_backoff=True,
    soft_time_limit=60,
    time_limit=120,
    name="parse_group"
)
def parse_group(self):
    """
    Задача получения информации о группе Steam
    """
    logger.info('Starting group info parse')
    
    try:
        group_href = 'https://steamcommunity.com/groups/vortexl4d4'
        href = f'{group_href}/memberslistxml/?xml=1'

        # Получение и парсинг XML
        response = httpx.get(href, timeout=10.0)
        response.raise_for_status()  # Проверка статуса ответа
        data = response.text

        root = ET.fromstring(data)
        root = root.find('groupDetails')
        
        if root is None:
            raise ValueError("Failed to find groupDetails in XML")

        # Извлечение данных
        membersCount = int(root.find('memberCount').text)
        membersInGame = int(root.find('membersInGame').text)
        membersOnline = int(root.find('membersOnline').text)

        # Сохранение в Redis
        group_data = {
            'membersCount': membersCount,
            'membersInGame': membersInGame,
            'membersOnline': membersOnline
        }
        
        try:
            with redis.Redis(connection_pool=redis_pool) as r:
                r.set('group_info', json.dumps(group_data), ex=3600)
        except redis.RedisError as e:
            logger.error(f"Redis error in parse_group: {str(e)}", exc_info=True)
            raise

        logger.info('Group info parsed and saved successfully')
        
    except (httpx.HTTPError, ET.ParseError, ValueError, redis.RedisError) as exc:
        logger.error(f"Error in parse_group: {str(exc)}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)
    except Exception as exc:
        logger.error(f"Unexpected error in parse_group: {str(exc)}", exc_info=True)
        raise