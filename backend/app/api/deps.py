from fastapi import Depends,HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from bson import ObjectId
from app.core.security import decode_access_token
from app.db.mongo import db
bearer=HTTPBearer(auto_error=False)
def current_user(credentials:HTTPAuthorizationCredentials=Depends(bearer)):
    if not credentials: raise HTTPException(401,'Authentication required')
    uid=decode_access_token(credentials.credentials)
    if not uid or not ObjectId.is_valid(uid): raise HTTPException(401,'Invalid or expired token')
    u=db.users.find_one(
        {'_id':ObjectId(uid)},
        {'password_hash':0,'recovery_answer_hash':0},
    )
    if not u: raise HTTPException(401,'Account not found')
    u['id']=str(u.pop('_id')); return u
