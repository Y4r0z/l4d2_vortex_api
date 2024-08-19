from dotenv import load_dotenv
from os import environ
load_dotenv(override=True)

SQL_CONNECT_STRING: str = environ.get('SQL_CONNECT_STRING') #type: ignore
STEAM_TOKEN: str = environ.get('STEAM_TOKEN') #type: ignore
SERVER_TOKEN: str = environ.get('SERVER_TOKEN') #type: ignore
REDIS_CONNECT_STRING: str = environ.get('REDIS_CONNECT_STRING') #type: ignore
REDIS_DATABASE: int = int(environ.get('REDIS_DATABASE')) #type: ignore
SOURCEBANS_CONNECT_STRING: str = environ.get('SOURCEBANS_CONNECT_STRING') #type: ignore


assert SQL_CONNECT_STRING is not None, 'SQL_CONNECT_STRING not set in environment variables'
assert STEAM_TOKEN is not None, 'STEAM_TOKEN not set in environment variables'
assert SERVER_TOKEN is not None, 'SERVER_TOKEN not set in environment variables'
assert REDIS_CONNECT_STRING is not None, 'REDIS_CONNECT_STRING not set in environment variables'
assert REDIS_DATABASE is not None, 'REDIS_DATABASE not set in environment variables'
assert SOURCEBANS_CONNECT_STRING is not None, 'SOURCEBANS_CONNECT_STRING not set in environment variables'
