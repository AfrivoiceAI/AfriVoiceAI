import hashlib
import logging
import secrets
import smtplib
import ssl
from datetime import datetime,timedelta,timezone
from email.message import EmailMessage
from urllib.parse import urlencode
from fastapi import APIRouter,HTTPException
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.db.mongo import db
from app.api.deps import current_user
from app.models.schemas import (
    LoginIn,
    PasswordResetIn,
    PasswordResetRequestIn,
    RecoveryQuestionLookupIn,
    RecoveryQuestionResetIn,
    RecoveryQuestionSetupIn,
    RegisterIn,
)
from app.core.security import hash_password,verify_password,create_access_token
from app.core.config import settings
router=APIRouter(prefix='/auth',tags=['authentication'])
logger=logging.getLogger(__name__)
RECOVERY_ATTEMPT_LIMIT=5
RECOVERY_LOCK_MINUTES=15

def normalize_recovery_answer(answer:str)->str:
    return ' '.join(answer.split()).casefold()

def validate_recovery_fields(question:str,answer:str)->tuple[str,str]:
    normalized_question=question.strip()
    normalized_answer=normalize_recovery_answer(answer)
    if len(normalized_question)<8:
        raise HTTPException(422,'Recovery question must be at least 8 characters')
    if len(normalized_answer)<8:
        raise HTTPException(422,'Recovery answer must be at least 8 non-space characters')
    return normalized_question,normalized_answer

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
    question,answer=validate_recovery_fields(data.recovery_question,data.recovery_answer)
    doc={'email':data.email.lower(),'display_name':data.display_name.strip(),'password_hash':hash_password(data.password),'recovery_question':question,'recovery_answer_hash':hash_password(answer),'tier':'free','usage_month':datetime.now(timezone.utc).strftime('%Y-%m'),'usage_count':0,'consent':{'platform_use':False,'evaluation':False,'model_training':False},'created_at':datetime.now(timezone.utc)}
    try: res=db.users.insert_one(doc)
    except DuplicateKeyError: raise HTTPException(409,'An account with this email already exists')
    uid=str(res.inserted_id); return {'access_token':create_access_token(uid),'token_type':'bearer','user':{'id':uid,'email':doc['email'],'display_name':doc['display_name'],'tier':'free','has_recovery_question':True}}
@router.post('/login')
def login(data:LoginIn):
    u=db.users.find_one({'email':data.email.lower()})
    if not u or not verify_password(data.password,u['password_hash']): raise HTTPException(401,'Incorrect email or password')
    uid=str(u['_id']); return {'access_token':create_access_token(uid),'token_type':'bearer','user':{'id':uid,'email':u['email'],'display_name':u['display_name'],'tier':u.get('tier','free'),'has_recovery_question':bool(u.get('recovery_answer_hash'))}}

@router.put('/recovery-question')
def set_recovery_question(data:RecoveryQuestionSetupIn,user=Depends(current_user)):
    account=db.users.find_one({'_id':ObjectId(user['id'])})
    if not account or not verify_password(data.current_password,account['password_hash']):
        raise HTTPException(401,'Current password is incorrect')

    question,answer=validate_recovery_fields(data.question,data.answer)
    db.users.update_one(
        {'_id':ObjectId(user['id'])},
        {'$set':{
            'recovery_question':question,
            'recovery_answer_hash':hash_password(answer),
        },'$unset':{
            'recovery_failed_attempts':'',
            'recovery_locked_until':'',
        }},
    )
    return {'has_recovery_question':True}

@router.post('/recovery-question')
def get_recovery_question(data:RecoveryQuestionLookupIn):
    account=db.users.find_one(
        {'email':data.email.lower()},
        {'recovery_question':1,'recovery_answer_hash':1},
    )
    if not account or not account.get('recovery_answer_hash'):
        raise HTTPException(404,'No recovery question is set for this account. Use email reset instead.')
    return {'question':account['recovery_question']}

@router.post('/reset-password-question')
def reset_password_with_question(data:RecoveryQuestionResetIn):
    account=db.users.find_one({'email':data.email.lower()})
    if not account or not account.get('recovery_answer_hash'):
        raise HTTPException(400,'Recovery details are invalid.')

    now=datetime.now(timezone.utc)
    locked_until=account.get('recovery_locked_until')
    if locked_until and locked_until>now:
        raise HTTPException(429,'Too many incorrect recovery attempts. Try again later.')
    if locked_until:
        db.users.update_one(
            {'_id':account['_id'],'recovery_locked_until':{'$lte':now}},
            {'$set':{'recovery_failed_attempts':0},
             '$unset':{'recovery_locked_until':''}},
        )

    answer=normalize_recovery_answer(data.answer)
    if not verify_password(answer,account['recovery_answer_hash']):
        db.users.update_one(
            {'_id':account['_id']},
            {'$inc':{'recovery_failed_attempts':1}},
        )
        attempts=db.users.find_one(
            {'_id':account['_id']},
            {'recovery_failed_attempts':1},
        ).get('recovery_failed_attempts',0)
        if attempts>=RECOVERY_ATTEMPT_LIMIT:
            db.users.update_one(
                {'_id':account['_id']},
                {'$set':{'recovery_locked_until':now+timedelta(minutes=RECOVERY_LOCK_MINUTES)}},
            )
            raise HTTPException(429,'Too many incorrect recovery attempts. Try again later.')
        raise HTTPException(400,'Recovery details are invalid.')

    result=db.users.update_one(
        {
            '_id':account['_id'],
            'recovery_answer_hash':account['recovery_answer_hash'],
            '$or':[
                {'recovery_locked_until':{'$exists':False}},
                {'recovery_locked_until':{'$lte':now}},
            ],
        },
        {'$set':{'password_hash':hash_password(data.password)},
         '$unset':{
             'password_reset_token_hash':'',
             'password_reset_expires_at':'',
             'recovery_failed_attempts':'',
             'recovery_locked_until':'',
         }},
    )
    if result.matched_count==0:
        raise HTTPException(400,'Recovery details are invalid.')
    return {'message':'Password reset successfully. You can now sign in.'}

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
