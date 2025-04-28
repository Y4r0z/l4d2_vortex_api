from src.settings import STEAM_TOKEN
import httpx
from typing import TypedDict

class PlayerSummary(TypedDict):
    steamid: str
    communityvisibilitystate: int
    profilestate: int
    personaname: str
    commentpermission: int
    profileurl: str
    avatar: str
    avatarmedium: str
    avatarfull: str
    avatarhash: str
    lastlogoff: int
    personastate: int
    realname: str
    primaryclanid: str
    timecreated: int
    personastateflags: int
    loccountrycode: str
    locstatecode: str


key = STEAM_TOKEN
host = 'https://api.steampowered.com'


async def GetPlayerSummaries(steam_id: str) -> PlayerSummary:
    """
    Получает информацию о профиле игрока по Steam ID
    """
    try:
        async with httpx.AsyncClient() as session:
            url = f'{host}/ISteamUser/GetPlayerSummaries/v0002/?key={key}&steamids={steam_id}'
            
            response = await session.get(url, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Steam API error: HTTP {response.status_code}")
            
            json = response.json()
            
            if not json or not json['response'] or not json['response']['players'] or len(json['response']['players']) == 0:
                raise Exception("Игрок не найден")
            
            player_data = json['response']['players'][0]
            
            return player_data
    except httpx.RequestError as e:
        raise Exception(f"Ошибка соединения с Steam API: {str(e)}")
    except Exception as e:
        raise


async def ResolveVanityURL(vanityURLName: str) -> str:
    """
    Возвращает SteamID по ссылке на профиль или чему-то еще.
    """
    try:
        async with httpx.AsyncClient() as session:
            url = f'{host}/ISteamUser/ResolveVanityURL/v1?key={key}&vanityurl={vanityURLName}'
            
            response = await session.get(url)
            
            if response.status_code != 200:
                raise Exception(f"Steam API error: HTTP {response.status_code}")
            
            json = response.json()
            
            if not json or not json['response'] or json['response']['success'] != 1:
                raise Exception('Игрок не найден')
            
            steam_id = json['response']['steamid']
            
            return steam_id
    except httpx.RequestError as e:
        raise Exception(f"Ошибка соединения с Steam API: {str(e)}")
    except Exception as e:
        raise