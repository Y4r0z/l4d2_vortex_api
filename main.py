from sqlalchemy import create_engine, MetaData
from sqlalchemy_utils import database_exists, create_database
from src.database.models import Base, engine
import uvicorn
from src.api.routes import api

def main():
    if not database_exists(engine.url): create_database(engine.url)
    Base.metadata.create_all(bind=engine)
    uvicorn.run(api, host='0.0.0.0', port='3005')



if __name__ == '__main__':
    main()