from pymongo import MongoClient,ASCENDING
from app.core.config import settings
client=MongoClient(settings.mongodb_url,serverSelectionTimeoutMS=5000)
db=client[settings.mongodb_database]
def ensure_indexes():
    db.users.create_index([("email",ASCENDING)],unique=True)
    db.generations.create_index([("user_id",ASCENDING),("created_at",-1)])
    db.feedback.create_index([("user_id",ASCENDING),("created_at",-1)])
def ping(): client.admin.command('ping')
