from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database
from src.database.models import Base, engine
import src.database.predefined as Predefiend
from fastapi import  FastAPI
from src.api.routes import api

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