from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import datetime
import jwt
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from src.api.tools import get_db, getOrCreateUser, requireToken, checkToken
from src.settings import SECRET_KEY
import src.lib.steam_api as SteamAPI

auth_api = APIRouter()
security = HTTPBearer()

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

def steamid64_to_steamid(steamid64: str) -> str:
    steamid64_int = int(steamid64)
    y = steamid64_int % 2
    z = (steamid64_int - 76561197960265728 - y) // 2
    return f"STEAM_1:{y}:{z}"

def steamid_to_steamid64(steamid: str) -> str:
    parts = steamid.split(":")
    if len(parts) != 3 or parts[0] != "STEAM_1":
        raise ValueError("Invalid SteamID format")
    
    y = int(parts[1])
    z = int(parts[2])
    steamid64 = z * 2 + 76561197960265728 + y
    return str(steamid64)

def create_jwt_token(user: Models.User) -> str:
    steam_id = steamid64_to_steamid(user.steamId) if len(user.steamId) == 17 else user.steamId
    now = datetime.datetime.now(datetime.timezone.utc)
    exp = now + datetime.timedelta(hours=JWT_EXPIRY_HOURS)
    
    payload = {
        "sub": user.id,
        "steam_id": steam_id,
        "exp": exp,
        "iat": now
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Models.User:
    payload = verify_jwt_token(credentials.credentials)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = db.query(Models.User).filter(Models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@auth_api.get('/check_token')
def check_token(db: Session = Depends(get_db), token: str = Depends(requireToken)):
    checkToken(db, token)
    return "token is valid"

@auth_api.post('/steam/verify', response_model=Schemas.SteamVerifyResponse)
async def verify_steam(
    steam_data: Schemas.SteamVerifyRequest,
    db: Session = Depends(get_db)
):
    try:
        steam_id_converted = steamid64_to_steamid(steam_data.steamid)
        user = getOrCreateUser(db, steam_id_converted)
        
        access_token = create_jwt_token(user)
        
        try:
            steam_info = await SteamAPI.GetPlayerSummaries(steam_data.steamid)
        except Exception:
            steam_info = {
                "steamid": steam_data.steamid,
                "personaname": steam_data.personaname,
                "avatar": steam_data.avatar,
                "avatarfull": steam_data.avatarfull or steam_data.avatar,
                "profileurl": steam_data.profileurl
            }
        
        privileges = Crud.get_privileges(db, user.id)
        
        return {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "steamId": user.steamId
            },
            "steamInfo": steam_info,
            "privileges": privileges
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Steam verification failed: {str(e)}")

@auth_api.get('/me', response_model=Schemas.AuthMeResponse)
async def get_current_user_info(
    current_user: Models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        steamid64 = steamid_to_steamid64(current_user.steamId)
        steam_info = await SteamAPI.GetPlayerSummaries(steamid64)
    except Exception:
        raise HTTPException(status_code=404, detail="Steam profile not found")
    
    privileges = Crud.get_privileges(db, current_user.id)
    
    return {
        "user": {
            "id": current_user.id,
            "steamId": current_user.steamId
        },
        "steamInfo": steam_info,
        "privileges": privileges
    }