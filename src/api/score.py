from fastapi import Depends, HTTPException, APIRouter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
from src.api.tools import getUser, requireToken, get_db, getOrCreateUser, checkToken
from src.api.filter import SeasonFilter, RoundScoreFilter
from typing import TypeVar
from sqlalchemy import func
from fastapi_filter import FilterDepends

score_api = APIRouter()

"""
TODO: search
"""

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