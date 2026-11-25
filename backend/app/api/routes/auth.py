from datetime import datetime,timezone
from fastapi import APIRouter,HTTPException
from pymongo.errors import DuplicateKeyError
from app.db.mongo import db
from app.models.schemas import RegisterIn,LoginIn
from app.core.security import hash_password,verify_password,create_access_token
router=APIRouter(prefix='/auth',tags=['authentication'])
@router.post('/register')
def register(data:RegisterIn):
    doc={'email':data.email.lower(),'display_name':data.display_name.strip(),'password_hash':hash_password(data.password),'tier':'free','usage_month':datetime.now(timezone.utc).strftime('%Y-%m'),'usage_count':0,'consent':{'platform_use':False,'evaluation':False,'model_training':False},'created_at':datetime.now(timezone.utc)}
    try: res=db.users.insert_one(doc)
    except DuplicateKeyError: raise HTTPException(409,'An account with this email already exists')
    uid=str(res.inserted_id); return {'access_token':create_access_token(uid),'token_type':'bearer','user':{'id':uid,'email':doc['email'],'display_name':doc['display_name'],'tier':'free'}}
@router.post('/login')
def login(data:LoginIn):
    u=db.users.find_one({'email':data.email.lower()})
    if not u or not verify_password(data.password,u['password_hash']): raise HTTPException(401,'Incorrect email or password')
    uid=str(u['_id']); return {'access_token':create_access_token(uid),'token_type':'bearer','user':{'id':uid,'email':u['email'],'display_name':u['display_name'],'tier':u.get('tier','free')}}
