from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database # type: ignore
from src.database.models import Base, engine, Balance
import src.database.predefined as Predefiend
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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
from src.api.info import info_api
from src.api.values import values_api
from src.middleware.rate_limiter import RateLimiter
from src.middleware.error_handler import ErrorHandler
from fastapi.responses import JSONResponse

async def createData():
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
    



app = FastAPI(
    title="API Vortex",
    version="1.0.0",
    lifespan=app_lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем rate limiter
app.middleware("http")(RateLimiter(requests_per_minute=60))

# Добавляем глобальный обработчик ошибок
app.middleware("http")(ErrorHandler())

# Добавляем health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Регистрируем роутеры с префиксом версии
api_prefix = "/api/v1"
app.include_router(api, prefix=api_prefix)
app.include_router(balance_api, prefix=f"{api_prefix}/balance")
app.include_router(discord_api, prefix=f"{api_prefix}/discord")
app.include_router(logs_api, prefix=f"{api_prefix}/logs")
app.include_router(score_api, prefix=f"{api_prefix}/score")
app.include_router(items_api, prefix=f"{api_prefix}/items")
app.include_router(inventory_api, prefix=f"{api_prefix}/inventory")
app.include_router(profile_api, prefix=f"{api_prefix}/profile")
app.include_router(sb_api, prefix=f"{api_prefix}/sourcebans")
app.include_router(info_api, prefix=f"{api_prefix}/info")
app.include_router(values_api, prefix=f"{api_prefix}/values")
