from dotenv import load_dotenv
from os import environ

load_dotenv(override=True)

# Database connections
SQL_CONNECT_STRING: str = environ.get('SQL_CONNECT_STRING') #type: ignore
SOURCEBANS_CONNECT_STRING: str = environ.get('SOURCEBANS_CONNECT_STRING') #type: ignore

# API Keys
STEAM_TOKEN: str = environ.get('STEAM_TOKEN') #type: ignore
SERVER_TOKEN: str = environ.get('SERVER_TOKEN') #type: ignore
SECRET_KEY: str = environ.get('SECRET_KEY') #type: ignore

# Redis settings
REDIS_CONNECT_STRING: str = environ.get('REDIS_CONNECT_STRING') #type: ignore
REDIS_DATABASE: int = int(environ.get('REDIS_DATABASE')) #type: ignore

# Celery settings
CELERY_BROKER_URL: str = environ.get('CELERY_BROKER_URL') #type: ignore
CELERY_RESULT_BACKEND: str = environ.get('CELERY_RESULT_BACKEND') #type: ignore

# New Celery configurations for better reliability
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 360
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_REDIS_MAX_CONNECTIONS = 20
CELERY_BROKER_CONNECTION_TIMEOUT = 10
CELERY_RESULT_EXTENDED = True

# Environment validation
assert SQL_CONNECT_STRING is not None, 'SQL_CONNECT_STRING not set in environment variables'
assert STEAM_TOKEN is not None, 'STEAM_TOKEN not set in environment variables'
assert SERVER_TOKEN is not None, 'SERVER_TOKEN not set in environment variables'
assert SECRET_KEY is not None, 'SECRET_KEY not set in environment variables'
assert REDIS_CONNECT_STRING is not None, 'REDIS_CONNECT_STRING not set in environment variables'
assert REDIS_DATABASE is not None, 'REDIS_DATABASE not set in environment variables'
assert SOURCEBANS_CONNECT_STRING is not None, 'SOURCEBANS_CONNECT_STRING not set in environment variables'
assert CELERY_BROKER_URL is not None, 'CELERY_BROKER_URL not set in environment variables'
assert CELERY_RESULT_BACKEND is not None, 'CELERY_RESULT_BACKEND not set in environment variables'