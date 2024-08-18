from rcon.source.async_rcon import rcon
from database.sourcebans import SbServer
from dataclasses import dataclass
import re


@dataclass
class RconPlayer:
    id: int
    name: str
    steam2id: str
    ip: str

def fromSteam64(sid : int | str) -> str:
    """
    Конвертирует SteamID64 в SteamID2 (для L4D2)
    """
    y = int(sid) - 76561197960265728
    x = y % 2 
    return(f"STEAM_1:{x}:{(y - x) // 2}")


playersRegex = re.compile(r'#\s*(\d+)(?>\s|\d)*"(.*)"\s*(STEAM_[01]:[01]:\d+|\[U:1:\d+\])(?>\s|:|\d)*[a-zA-Z]*\s*\d*\s([0-9.]+)')
def parsePlayers(status: str) -> list[RconPlayer]:
    """
    Парсит список игроков из rcon `status` 
    """
    result = []
    for i in playersRegex.findall(status):
        result.append(RconPlayer(i[0], i[1], i[2], i[3]))
    return result

async def rconCommand(server: SbServer, command: str, *args: str) -> str:
    response = await rcon(
        command, *args,
        host = server.ip, port = server.port, passwd = server.rcon
    )
    return response

async def kickPlayer(servers: list[SbServer], steam2id: str) -> None:
    breakflag = False
    for server in servers:
        if breakflag: break
        try:
            status = await rconCommand(server, 'status')
        except:
            continue
        players = parsePlayers(status)
        for p in players:
            if p.steam2id != steam2id: continue
            try:
                await rconCommand(server, 'sm_kick', f'#{p.id}')
            except:
                continue
            print(f'Kicked player {p.name} from {server.ip}:{server.port}')
            breakflag = True
            break