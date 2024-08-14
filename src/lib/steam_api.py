from src.settings import STEAM_TOKEN
import httpx
from pydantic_core import from_json
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
    async with httpx.AsyncClient() as session:
        response = await session.get(f'{host}/ISteamUser/GetPlayerSummaries/v0002/?key={key}&steamids={steam_id}', timeout=30)
        json = response.json()
        if not json or not json['response'] or not json['response']['players'] or len(json['response']['players']) == 0:
                raise Exception("Игрок не найден")
        return json['response']['players'][0]

async def ResolveVanityURL(vanityURLName: str) -> str:
    """
    Возвращает SteamID по ссылке на профиль или чему-то еще.
    """
    async with httpx.AsyncClient() as session:
        response = await session.get(f'{host}/ISteamUser/ResolveVanityURL/v1?key={key}&vanityurl={vanityURLName}')
        json = response.json()
        if not json or not json['response'] or json['response']['success'] != 1:
            raise Exception('Игрок не найден')
        return json['response']['steamid']
