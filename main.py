from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database
from src.database.models import Base, engine
import src.database.predefined as Predefiend
from fastapi import  FastAPI
from src.api.routes import api
from src.api.balance import balance_api
from src.api.discord import discord_api

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
Base.metadata.create_all(bind=engine)
createData()
app = FastAPI()
app.include_router(api)
app.include_router(balance_api, prefix='/balance')
app.include_router(discord_api, prefix='/discord')