from rcon.source.async_rcon import rcon as arcon #type: ignore
from rcon.source import Client #type: ignore
from src.database.sourcebans import SbServer, SbBan, AsyncSession
from dataclasses import dataclass
import time
from sqlalchemy import select
import re

class BanExistsError(Exception):
    ...

@dataclass
class RconPlayer:
    id: int
    name: str
    steam2id: str
    ip: str
    steam64id: str

def fromSteam64(sid : int | str) -> str:
    """
    Конвертирует SteamID64 в SteamID2 (для L4D2)
    """
    y = int(sid) - 76561197960265728
    x = y % 2 
    return(f"STEAM_1:{x}:{(y - x) // 2}")

def toSteam64(sid: str) -> str:
    splitted = sid.split(':')
    a = int(splitted[1])
    b = int(splitted[2])
    return str(76561197960265728 + (b*2) + a)


playersRegex = re.compile(r'#\s*(\d+)(?>\s|\d)*"(.*)"\s*(STEAM_[01]:[01]:\d+|\[U:1:\d+\])(?>\s|:|\d)*[a-zA-Z]*\s*\d*\s([0-9.]+)')
def parsePlayers(status: str) -> list[RconPlayer]:
    """
    Парсит список игроков из rcon `status` 
    """
    result = []
    for i in playersRegex.findall(status):
        result.append(RconPlayer(i[0], i[1], i[2], i[3], toSteam64(i[2])))
    return result

async def rconCommandAsync(server: SbServer, command: str, *args: str) -> str:
    response = await arcon(
        command, *args,
        host = server.ip, port = server.port, passwd = server.rcon
    )
    return response

def rconCommand(server: SbServer, command: str, *args: str) -> str:
    with Client(server.ip, server.port, passwd = server.rcon) as client:
        response = client.run(command, *args)
    return response

def getRconPlayers(server: SbServer) -> list[RconPlayer]:
    status = rconCommand(server, 'status')
    return parsePlayers(status)

async def kickPlayer(servers: list[SbServer], steam2id: str, reason: str = 'Вы были кикнуты') -> None:
    breakflag = False
    for server in servers:
        if breakflag: break
        try:
            status = await rconCommandAsync(server, 'status')
        except:
            continue
        players = parsePlayers(status)
        for p in players:
            if p.steam2id != steam2id: continue
            try:
                await rconCommandAsync(server, 'sm_kick', f'#{p.id}', reason)
            except:
                continue
            print(f'Kicked player {p.name} from {server.ip}:{server.port}')
            breakflag = True
            break

async def banPlayer(sb: AsyncSession, steamid64: str, duration: int, reason: str, name: str = 'api_ban'):
    now = int(time.time())
    authid = fromSteam64(steamid64) 
    # Проверка на наличие банов
    query = select(SbBan).filter(SbBan.authid == authid, SbBan.ends > now)
    prevBan = (await sb.execute(query)).first()
    if prevBan is not None:
        raise BanExistsError(f'Player {name} already has a ban')
    # Добавление бана
    ban = SbBan(adminIp='0.0.0.1', authid=authid, name=name,
                reason=reason, aid=0, sid=0, type=0,
                created=now, ends=now+duration, length=duration)
    sb.add(ban)
    await sb.commit()
    # Кик игрока с серверов
    query2 = select(SbServer)
    servers = [s._tuple()[0] for s in (await sb.execute(query2)).all()]
    await kickPlayer(servers, authid, reason=f'Бан: {reason}')
    