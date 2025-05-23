from fastapi import Depends, HTTPException, APIRouter
from src.database import models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from sqlalchemy import func, select, text, Integer
from typing import List
import datetime
import calendar
from src.api.tools import requireToken, get_db, getOrCreateUser, checkToken, getRedis, getUser
from src.api.filter import SeasonFilter, RoundScoreFilter, Pagination
from src.api.balance import getOrCreateBalance
from typing import TypeVar
from fastapi_filter import FilterDepends
from redis.asyncio import Redis
import src.lib.steam_api as SteamAPI
from sqlalchemy.sql.expression import cast
import src.database.crud as Crud
import json
import asyncio



PROFILE_CACHE_TIME = 3600
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

@score_api.get('/session/top', response_model=List[Schemas.TopPlaytime])
async def get_top_playtime(
    limit: int = 10,
    db: Session = Depends(get_db),
    redis: Redis = Depends(getRedis)
):
    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be at least 1")
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be at most 100")
    
    cache_key = f"playtime_top:{limit}"
    cached_result = await redis.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    subquery = db.query(
        Models.PlaySession.userId,
        func.sum(
            func.timestampdiff(text('SECOND'), Models.PlaySession.timeFrom, Models.PlaySession.timeTo)
        ).label('total_seconds')
    ).filter(
        Models.PlaySession.timeTo.isnot(None)
    ).group_by(Models.PlaySession.userId).subquery()
    
    query = db.query(
        func.dense_rank().over(
            order_by=subquery.c.total_seconds.desc()
        ).label('rank'),
        Models.User.steamId,
        subquery.c.total_seconds
    ).join(
        Models.User, Models.User.id == subquery.c.userId
    ).filter(
        subquery.c.total_seconds.isnot(None)
    ).order_by(
        subquery.c.total_seconds.desc()
    ).limit(limit)
    
    results = query.all()
    
    response = [
        {
            'rank': int(row[0]),
            'steam_id': row[1],
            'total_seconds': int(row[2]) if row[2] else 0,
            'total_hours': round(float(row[2]) / 3600, 2) if row[2] else 0.0
        }
        for row in results
    ]
    
    await redis.set(cache_key, json.dumps(response), ex=300)
    
    return response

@score_api.get('/session/playtime', response_model=Schemas.PlayTime)
def get_total_playtime(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    
    sessions = db.query(Models.PlaySession).filter(
        Models.PlaySession.userId == user.id
    ).all()
    
    total_seconds = 0
    for session in sessions:
        if session.timeTo and session.timeFrom:
            duration = session.timeTo - session.timeFrom
            total_seconds += int(duration.total_seconds())
    
    total_hours = round(total_seconds / 3600, 2)
    
    return {
        'steam_id': steam_id,
        'total_seconds': total_seconds,
        'total_hours': total_hours
    }

async def distribute_season_rewards(db: Session, date: datetime.date, redis: Redis):
    try:
        top_players_query = db.query(
            Models.User.id, 
            Models.User.steamId, 
            func.sum(Models.RoundScore.agression + Models.RoundScore.support + Models.RoundScore.perks).label('total_score')
        ).join(
            Models.RoundScore, 
            Models.User.id == Models.RoundScore.userId
        ).group_by(
            Models.User.id, 
            Models.User.steamId
        ).order_by(
            func.sum(Models.RoundScore.agression + Models.RoundScore.support + Models.RoundScore.perks).desc()
        ).limit(3)
                    
        top_players = top_players_query.all()
        
        if not top_players:
            return []
        
        last_day_of_month = calendar.monthrange(date.year, date.month)[1]
        end_of_month = datetime.datetime.combine(
            datetime.date(date.year, date.month, last_day_of_month),
            datetime.time(22, 0),
            tzinfo=datetime.timezone.utc
        )
        
        rewards = [
            {"position": 1, "privilege_id": 8, "coins": 100000, "privilege_name": "legend"},
            {"position": 2, "privilege_id": 7, "coins": 50000, "privilege_name": "premium"},
            {"position": 3, "privilege_id": 6, "coins": 25000, "privilege_name": "vip"}
        ]
        
        reward_results = []
        
        for i, player in enumerate(top_players):
            if i < len(rewards):
                user_id = player[0]
                steam_id = player[1]
                score = player[2]
                reward = rewards[i]
                
                user = getUser(db, steam_id)
                user_privileges = Crud.get_privileges(db, user.id)
                
                has_privilege = getattr(user_privileges, reward["privilege_name"], False)
                
                if has_privilege:
                    balance = getOrCreateBalance(db, user)
                    balance.value += reward["coins"]
                    
                    transaction = Models.Transaction(
                        balance=balance, 
                        value=reward["coins"], 
                        description=f'Season top-{reward["position"]} reward'
                    )
                    db.add(transaction)
                    
                    reward_results.append({
                        "position": reward["position"],
                        "steam_id": steam_id,
                        "reward_type": "coins",
                        "amount": reward["coins"]
                    })
                else:
                    Crud.add_privilege(db, user_id, reward["privilege_id"], end_of_month)
                    
                    reward_results.append({
                        "position": reward["position"],
                        "steam_id": steam_id,
                        "reward_type": "privilege",
                        "privilege": reward["privilege_name"],
                        "until": end_of_month.isoformat()
                    })
        
        return reward_results
    except Exception as e:
        db.rollback()
        raise e


@score_api.post('/season/reset')
async def initiate_season(date: datetime.date | None = None, db: Session = Depends(get_db), token: str = Depends(requireToken), redis: Redis = Depends(getRedis)):
    """
    Подсчитывает итоги сезона.
    Учитывает все очки что есть в БД и удаляет их, взамег создавая запись в таблице сезона
    """
    checkToken(db, token)
    
    current_date = date or datetime.date.today()
    
    try:
        reward_results = await distribute_season_rewards(db, current_date, redis)
        
        RS = Models.RoundScore
        fsum = func.sum
        sel = db.query(RS.userId, fsum(RS.agression), fsum(RS.support), fsum(RS.perks)).group_by(RS.userId)
        for result in sel:
            db.add(Models.ScoreSeason(userId=result[0], agression=result[1], support=result[2], perks=result[3], date=current_date))
        for score in db.query(Models.RoundScore):
            db.add(Models.RoundScorePermanent(userId=score.userId, agression=score.agression, support=score.support, perks=score.perks, time=score.time, team=score.team))
        db.query(Models.RoundScore).delete()
        db.commit()
        
        top_keys = await redis.keys("top:*")
        if top_keys:
            await redis.delete(*top_keys)
        
        rank_keys = await redis.keys("game_rank:*")
        if rank_keys:
            await redis.delete(*rank_keys)
            
        return {
            'message': 'Season reset and rewards distributed!',
            'rewards': reward_results
        }
    except Exception as e:
        db.rollback()
        return {'message': 'Season reset failed', 'error': str(e)}

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
    result = sorted(result, key=lambda x: x['rank'])
    await redis.set(rkey, json.dumps(result), ex=TOP_CACHE_TIME)
    return result



"""
select * from
(select userId, dense_rank() over (order by sum(agression + support + perks) desc) as 'rank' from roundScore group by userId) tbl
where userId = USER_ID;
"""
@score_api.get('/top/rank', response_model=Schemas.Rank)
def get_player_top_rank(steam_id: str, db: Session = Depends(get_db)):
    user = getUser(db, steam_id)
    result = Crud.get_player_rank_score(db, user)
    if result is None: raise HTTPException(status_code=404, detail=f"Player ({steam_id}) has no score data.")
    return {
        'rank': result[0],
        'score': result[1]
    }
        
        
@score_api.get('/game/rank', response_model=Schemas.Rank)
async def get_game_player_rank(steam_id: str, db: Session = Depends(get_db), redis: Redis = Depends(getRedis)):
    try:
        cache_key = f"game_rank:{steam_id}"
        
        cached_result = await redis.get(cache_key)
        if cached_result is not None:
            cached_data = json.loads(cached_result)
            if cached_data == "no_data":
                raise HTTPException(status_code=404, detail=f"Player ({steam_id}) has no score data.")
            return cached_data
        
        user = getUser(db, steam_id)
        
        has_scores = db.query(Models.RoundScore).filter(Models.RoundScore.userId == user.id).limit(1).count() > 0
        if not has_scores:
            await redis.set(cache_key, json.dumps("no_data"), ex=120)
            raise HTTPException(status_code=404, detail=f"Player ({steam_id}) has no score data.")
        
        result = Crud.get_player_rank_score(db, user)
        
        if result is None:
            await redis.set(cache_key, json.dumps("no_data"), ex=120)
            raise HTTPException(status_code=404, detail=f"Player ({steam_id}) has no score data.")
        
        rank_data = {
            'rank': int(result[0]),
            'score': int(result[1])
        }
        
        await redis.set(cache_key, json.dumps(rank_data), ex=300)
        
        return rank_data
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Error retrieving player rank data: {str(e)}")