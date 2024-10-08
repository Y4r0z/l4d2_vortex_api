import a2s # type: ignore
from src.database.sourcebans import SbServer
from dataclasses import dataclass

# Не имеет смысла брать отсюда игроков из-за отсутствия Steam ID 

@dataclass
class A2SServer:
    server_name: str
    map_name: str
    player_count: int
    max_players: int
    ping: float
    keywords: str

@dataclass
class A2SPlayer:
    index: int
    name: str
    score: int
    duration: float
    

async def getServerInfoAsync(server: SbServer) -> A2SServer:
    address = (server.ip, server.port)
    info = await a2s.ainfo(address, encoding='utf-8')
    return A2SServer(
        info.server_name,
        info.map_name,
        info.player_count,
        info.max_players,
        info.ping,
        keywords=info.keywords
    )

def getServerInfo(server: SbServer) -> A2SServer:
    address = (server.ip, server.port)
    info = a2s.info(address, encoding='utf-8')
    return A2SServer(
        info.server_name,
        info.map_name,
        info.player_count,
        info.max_players,
        info.ping,
        keywords=info.keywords
    )

def getServerPlayers(server: SbServer) -> list[A2SPlayer]:
    address = (server.ip, server.port)
    players = a2s.players(address, timeout=5, encoding='utf-8')
    return [
        A2SPlayer(i.index, i.name, i.score, i.duration) 
        for i in players
    ]