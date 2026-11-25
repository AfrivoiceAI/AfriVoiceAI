from datetime import datetime,timedelta,timezone
import jwt
from pwdlib import PasswordHash
from app.core.config import settings
_hasher=PasswordHash.recommended()
def hash_password(p:str)->str: return _hasher.hash(p)
def verify_password(p:str,h:str)->bool: return _hasher.verify(p,h)
def create_access_token(subject:str)->str:
    exp=datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub":subject,"exp":exp},settings.jwt_secret,algorithm=settings.jwt_algorithm)
def decode_access_token(token:str):
    try: return jwt.decode(token,settings.jwt_secret,algorithms=[settings.jwt_algorithm]).get('sub')
    except jwt.PyJWTError: return None
