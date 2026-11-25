from datetime import datetime,timezone
from bson import ObjectId
from fastapi import APIRouter,Depends,HTTPException,UploadFile,File
from app.api.deps import current_user
from app.db.mongo import db
from app.models.schemas import GenerationIn
from app.services.ai import text_generate,speech_generate,image_generate,transcribe
from app.core.config import settings
router=APIRouter(prefix='/generations',tags=['generations'])
def charge(uid):
    u=db.users.find_one({'_id':ObjectId(uid)}); month=datetime.now(timezone.utc).strftime('%Y-%m')
    count=u.get('usage_count',0) if u.get('usage_month')==month else 0
    if count>=settings.monthly_generation_limit: raise HTTPException(429,'Monthly free generation limit reached')
    db.users.update_one({'_id':ObjectId(uid)},{'$set':{'usage_month':month},'$inc':{'usage_count':1}}); return count+1
@router.post('')
async def create(data:GenerationIn,user=Depends(current_user)):
    used=charge(user['id'])
    if data.kind=='text': out=await text_generate(data.prompt)
    elif data.kind=='speech': out=await speech_generate(data.prompt,data.language)
    else: out=await image_generate(data.prompt)
    doc={'user_id':user['id'],'kind':data.kind,'prompt':data.prompt,'language':data.language,'output':out,'created_at':datetime.now(timezone.utc)}
    res=db.generations.insert_one(doc); return {'id':str(res.inserted_id),**doc,'usage_count':used}
@router.post('/transcribe')
async def transcribe_audio(file:UploadFile=File(...),user=Depends(current_user)):
    if not (file.content_type or '').startswith('audio/'): raise HTTPException(415,'Upload an audio file')
    if file.size and file.size>settings.max_upload_mb*1024*1024: raise HTTPException(413,'File too large')
    used=charge(user['id']); out=await transcribe(file); res=db.generations.insert_one({'user_id':user['id'],'kind':'transcription','prompt':file.filename,'output':out,'created_at':datetime.now(timezone.utc)})
    return {'id':str(res.inserted_id),'output':out,'usage_count':used}
@router.get('')
def history(user=Depends(current_user)):
    rows=list(db.generations.find({'user_id':user['id']}).sort('created_at',-1).limit(50))
    for d in rows: d['id']=str(d.pop('_id'))
    return rows
@router.get('/usage')
def usage(user=Depends(current_user)):
    d=db.users.find_one({'_id':ObjectId(user['id'])}); m=datetime.now(timezone.utc).strftime('%Y-%m'); return {'used':d.get('usage_count',0) if d.get('usage_month')==m else 0,'limit':settings.monthly_generation_limit,'month':m}
