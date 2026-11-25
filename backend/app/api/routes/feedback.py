from datetime import datetime,timezone
from bson import ObjectId
from fastapi import APIRouter,Depends
from app.api.deps import current_user
from app.db.mongo import db
from app.models.schemas import FeedbackIn,ConsentIn
router=APIRouter(tags=['feedback and consent'])
@router.post('/feedback')
def feedback(data:FeedbackIn,user=Depends(current_user)):
    r=db.feedback.insert_one({**data.model_dump(),'user_id':user['id'],'created_at':datetime.now(timezone.utc)}); return {'id':str(r.inserted_id),'message':'Thanks for your feedback'}
@router.put('/consent')
def consent(data:ConsentIn,user=Depends(current_user)):
    db.users.update_one({'_id':ObjectId(user['id'])},{'$set':{'consent':{**data.model_dump(),'updated_at':datetime.now(timezone.utc)}}}); return {'consent':data.model_dump()}
