from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.db.mongo import ensure_indexes,ping
from app.api.routes import auth,generations,feedback
Path('uploads').mkdir(exist_ok=True)
app=FastAPI(title=settings.app_name,version='0.1.0')
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins_list,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.mount('/media',StaticFiles(directory='uploads'),name='media')
app.include_router(auth.router,prefix=settings.api_prefix); app.include_router(generations.router,prefix=settings.api_prefix); app.include_router(feedback.router,prefix=settings.api_prefix)
@app.on_event('startup')
def startup(): ensure_indexes()
@app.get('/health')
def health():
    try: ping(); return {'status':'ok','database':'connected'}
    except Exception: return {'status':'degraded','database':'unavailable'}
@app.get('/')
def root(): return {'name':settings.app_name,'docs':'/docs'}
