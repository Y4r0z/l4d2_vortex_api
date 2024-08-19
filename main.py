from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database # type: ignore
from src.database.models import Base, engine, Balance
import src.database.predefined as Predefiend
from fastapi import  FastAPI
from src.api.routes import api
from src.api.balance import balance_api
from src.api.discord import discord_api
from src.api.chat_logs import logs_api
from src.api.score import score_api
from src.api.items import items_api
from src.api.inventory import inventory_api
from src.api.tools import app_lifespan
from src.api.profile import profile_api
from src.api.sourcebans import sb_api

def createData():
    with Session(engine) as session:
        for i in Predefiend.Users.values():
            session.merge(i)
        for i in Predefiend.PrivilegeTypes.values():
            session.merge(i)
        for i in Predefiend.Privileges.values():
            session.merge(i)
        for i in Predefiend.AuthTokens.values():
            session.merge(i)
        session.commit()


if not database_exists(engine.url): create_database(engine.url)

try:
    createData()
except:
    print('Can not create initial data in database')
    



app = FastAPI(lifespan=app_lifespan)
app.include_router(api)
app.include_router(balance_api, prefix='/balance')
app.include_router(discord_api, prefix='/discord')
app.include_router(logs_api, prefix='/logs')
app.include_router(score_api, prefix='/score')
app.include_router(items_api, prefix='/items')
app.include_router(inventory_api, prefix='/inventory')
app.include_router(profile_api, prefix='/profile')
app.include_router(sb_api, prefix='/sourcebans')

