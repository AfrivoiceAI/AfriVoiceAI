import hashlib
import logging
import secrets
import smtplib
import ssl
from datetime import datetime,timedelta,timezone
from email.message import EmailMessage
from urllib.parse import urlencode
from fastapi import APIRouter,HTTPException
from pymongo.errors import DuplicateKeyError
from app.db.mongo import db
from app.models.schemas import RegisterIn,LoginIn,PasswordResetIn,PasswordResetRequestIn
from app.core.security import hash_password,verify_password,create_access_token
from app.core.config import settings
router=APIRouter(prefix='/auth',tags=['authentication'])
logger=logging.getLogger(__name__)

def send_password_reset_email(email:str,token:str):
    message=EmailMessage()
    message['Subject']='Reset your AfriVoiceAI password'
    message['From']=settings.smtp_from_email
    message['To']=email
    reset_url=f"{settings.frontend_url.rstrip('/')}/?{urlencode({'reset_token':token})}"
    message.set_content(
        f"Use this link to reset your AfriVoiceAI password. It expires in one hour:\n\n"
        f"{reset_url}\n\nIf you did not request a password reset, you can ignore this email."
    )
    with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=10) as server:
        server.starttls(context=ssl.create_default_context())
        if settings.smtp_username:
            server.login(settings.smtp_username,settings.smtp_password)
        server.send_message(message)

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

@router.post('/forgot-password')
def forgot_password(data:PasswordResetRequestIn):
    if not settings.smtp_host or not settings.smtp_from_email:
        raise HTTPException(503,'Password reset email is not configured. Set SMTP_HOST and SMTP_FROM_EMAIL.')
    if bool(settings.smtp_username)!=bool(settings.smtp_password):
        raise HTTPException(503,'Password reset email credentials are incomplete. Set both SMTP_USERNAME and SMTP_PASSWORD.')

    user=db.users.find_one({'email':data.email.lower()})
    if not user:
        return {'message':'If an account exists for this email, a password reset link will be sent.'}

    token=secrets.token_urlsafe(32)
    now=datetime.now(timezone.utc)
    db.users.update_one(
        {'_id':user['_id']},
        {'$set':{
            'password_reset_token_hash':hashlib.sha256(token.encode()).hexdigest(),
            'password_reset_expires_at':now+timedelta(hours=1),
        }},
    )
    try:
        send_password_reset_email(user['email'],token)
    except Exception as error:
        logger.exception('Could not send password reset email')
        db.users.update_one(
            {'_id':user['_id'],'password_reset_token_hash':hashlib.sha256(token.encode()).hexdigest()},
            {'$unset':{'password_reset_token_hash':'','password_reset_expires_at':''}},
        )
        raise HTTPException(503,'Password reset email could not be sent. Please try again later.') from error
    return {'message':'If an account exists for this email, a password reset link will be sent.'}

@router.post('/reset-password')
def reset_password(data:PasswordResetIn):
    now=datetime.now(timezone.utc)
    token_hash=hashlib.sha256(data.token.encode()).hexdigest()
    result=db.users.update_one(
        {
            'password_reset_token_hash':token_hash,
            'password_reset_expires_at':{'$gt':now},
        },
        {'$set':{'password_hash':hash_password(data.password)},
         '$unset':{'password_reset_token_hash':'','password_reset_expires_at':''}},
    )
    if result.matched_count == 0:
        raise HTTPException(400,'This password reset link is invalid or has expired. Request a new link.')
    return {'message':'Password reset successfully. You can now sign in.'}
