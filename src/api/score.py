from fastapi import Depends, HTTPException, APIRouter
from src.database import models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import datetime
from src.api.tools import requireToken, get_db, getOrCreateUser, checkToken, getRedis, getUser
from src.api.filter import SeasonFilter, RoundScoreFilter, Pagination
from typing import TypeVar
from sqlalchemy import func, select
from fastapi_filter import FilterDepends
from redis.asyncio import Redis # type: ignore
import src.lib.steam_api as SteamAPI
from sqlalchemy.sql.expression import cast
from sqlalchemy import Integer
import json
import asyncio



PROFILE_CACHE_TIME = 86400
TOP_CACHE_TIME = 3600

score_api = APIRouter()


T = TypeVar('T', bound=Models.IDModel)
def createObj(steam_id: str, schemaObj: Schemas.BaseModel, db: Session, token: str, model: type[T]) -> T:
    checkToken(db, token)
    user = getOrCreateUser(db, steam_id)
    obj = model(**(schemaObj.model_dump()), user=user)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def getObj(obj_id: int, db: Session, model: type[T]) -> T:
    if (obj := (db.query(model).filter(model.id == obj_id).first())) is None:
        raise HTTPException(404, f'Object ({model.__tablename__}) with id {obj_id} not found!')
    return obj



@score_api.post('/round', response_model=Schemas.RoundScore.Output)
def add_round_score(steam_id: str, score: Schemas.RoundScore.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    return createObj(steam_id, score, db, token, Models.RoundScore)

@score_api.get('/round', response_model=Schemas.RoundScore.Output)
def get_round_score(score_id: int, db: Session = Depends(get_db)):
    return getObj(score_id, db, Models.RoundScore)

@score_api.get('/round/search', response_model=List[Schemas.RoundScore.Output])
def search_round_scores(score_filter: RoundScoreFilter = FilterDepends(RoundScoreFilter), db: Session = Depends(get_db)):
    query = db.query(Models.RoundScore).join(Models.User)
    query = score_filter.filter(query)
    query = score_filter.sort(query)
    return query.all()

@score_api.post('/session', response_model=Schemas.PlaySession.Output)
def add_play_session(steam_id: str, session: Schemas.PlaySession.Input, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    return createObj(steam_id, session, db, token, Models.PlaySession)

@score_api.get('/session', response_model=Schemas.PlaySession.Output)
def get_play_session(session_id: int, db: Session = Depends(get_db)):
    return getObj(session_id, db, Models.PlaySession)

@score_api.post('/season/reset')
def initiate_season(date: datetime.date | None = None, db: Session = Depends(get_db), token: str = Depends(requireToken)):
    """
    Подсчитывает итоги сезона.
    Учитывает все очки что есть в БД и удаляет их, взамег создавая запись в таблице сезона
    """
    checkToken(db, token)
    RS = Models.RoundScore
    fsum = func.sum
    sel = db.query(RS.userId, fsum(RS.agression), fsum(RS.support), fsum(RS.perks)).group_by(RS.userId)
    for result in sel:
        db.add(Models.ScoreSeason(userId=result[0], agression=result[1], support=result[2], perks=result[3], date=datetime.date.today() if date is None else date))
    for score in db.query(Models.RoundScore):
        db.add(Models.RoundScorePermanent(userId=score.userId, agression=score.agression, support=score.support, perks=score.perks, time=score.time, team=score.team))
    db.query(Models.RoundScore).delete()
    db.commit()
    return {'message': 'done!'}

@score_api.get('/season/search', response_model=List[Schemas.ScoreSeason.Output])
def search_seasons(season_filter: SeasonFilter = FilterDepends(SeasonFilter), db: Session = Depends(get_db)):
    query = db.query(Models.ScoreSeason).join(Models.User)
    query = season_filter.filter(query)
    query = season_filter.sort(query)
    return query.all()



# select dense_rank() over (order by sum(agression + support + perks) desc) as 'rank', 
# user.steamId, sum(agression + support + perks) as score 
# from roundScore 
# left join user on user.id = roundScore.userId 
# group by steamId 
# order by score desc;

async def createTopList(item: tuple[int, str, int], result: list, redis: Redis):
    steamId = item[1]
    rkey = f'steam:{steamId}'
    if (steamInfo:=(await redis.get(rkey))) is None:      
        steamInfo = await SteamAPI.GetPlayerSummaries(steamId)
        await redis.set(rkey, json.dumps(steamInfo), ex=PROFILE_CACHE_TIME)
    else:
        steamInfo = json.loads(steamInfo)
    result.append(
        {
        'rank':     item[0],
        'steamId':  steamId,
        'score':    item[2],
        'steamInfo': steamInfo
        }
    )

"""
TODO: Steam API per player, cache redis per player (ex: 3days)
"""
@score_api.get('/top', response_model=None)
async def get_top_scores(
    pagination: Pagination = Depends(Pagination), 
    db: Session = Depends(get_db), 
    redis: Redis = Depends(getRedis)
):
    if pagination.limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be less than or equal to 100.")
    rkey = f'top:{pagination.limit}:{pagination.offset}'
    if (data:=(await redis.get(rkey))) is not None:
        return json.loads(data)
    top = select(
        func.dense_rank().over(order_by=func.sum(Models.RoundScore.agression + Models.RoundScore.support + Models.RoundScore.perks).desc()),
        Models.User.steamId,
        cast(func.sum(Models.RoundScore.agression + Models.RoundScore.support + Models.RoundScore.perks), Integer)
    ).join(Models.User, Models.User.id == Models.RoundScore.userId) \
    .group_by(Models.User.steamId) \
    .order_by(func.sum(Models.RoundScore.agression + Models.RoundScore.support +Models.RoundScore.perks).desc())
    query = pagination.paginate(top)
    queryResult = db.execute(query)
    result : list[dict] = []
    tasks = [createTopList(i, result, redis) for i in queryResult]
    await asyncio.gather(*tasks)
    await redis.set(rkey, json.dumps(result), ex=TOP_CACHE_TIME)
    return result



"""
select * from
(select userId, dense_rank() over (order by sum(agression + support + perks) desc) as 'rank' from roundScore group by userId) tbl
where userId = USER_ID;
"""
@score_api.get('/top/rank', response_model=int)
def get_player_top_rank(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    subquery = select(
        Models.RoundScore.userId, 
        func.dense_rank().over(order_by=func.sum(Models.RoundScore.agression + Models.RoundScore.support + Models.RoundScore.perks).desc()).label('rank')
    ).group_by(Models.RoundScore.userId).alias('tbl')
    query = select(subquery.c.rank).where(subquery.c.userId == user.id)
    result = db.execute(query).first()
    if result is None: raise HTTPException(status_code=404, detail=f"Player ({steam_id}) has no score data.")
    return result[0]
        
        
    