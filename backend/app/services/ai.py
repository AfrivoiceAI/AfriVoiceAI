import uuid
from pathlib import Path
import httpx
from fastapi import HTTPException,UploadFile
from app.core.config import settings
UPLOADS=Path('uploads'); UPLOADS.mkdir(exist_ok=True)
async def text_generate(prompt:str):
    if settings.ai_mode!='local': return {'status':'demo','text':'[Demo output] '+prompt+'\n\nEnable Ollama and AI_MODE=local to run a local model.'}
    try:
        async with httpx.AsyncClient(timeout=180) as c:
            r=await c.post(settings.ollama_base_url.rstrip('/')+'/api/generate',json={'model':settings.ollama_model,'prompt':prompt,'stream':False}); r.raise_for_status(); return {'status':'completed','text':r.json().get('response',''),'model':settings.ollama_model}
    except Exception as e: raise HTTPException(503,f'Ollama unavailable: {e}')
async def speech_generate(prompt:str,language:str):
    if settings.tts_provider!='kokoro': return {'status':'demo','message':'Speech demo mode. Configure Kokoro for English speech.'}
    if language not in ('en','en-NG'): raise HTTPException(501,'This model is not validated for this language yet.')
    try:
        from kokoro import KPipeline
        import soundfile as sf, numpy as np
        pipe=KPipeline(lang_code='a'); chunks=[audio for _,_,audio in pipe(prompt,voice='af_heart',speed=1)]
        if not chunks: raise RuntimeError('No audio generated')
        name=f'{uuid.uuid4()}.wav'; sf.write(str(UPLOADS/name),np.concatenate(chunks),24000)
        return {'status':'completed','media_url':'/media/'+name,'model':'Kokoro-82M'}
    except ImportError: raise HTTPException(503,'Install requirements-audio.txt to enable Kokoro.')
    except Exception as e: raise HTTPException(503,f'Kokoro failed: {e}')
async def image_generate(prompt:str):
    if settings.image_provider!='flux': return {'status':'demo','message':'Image demo mode. Configure FLUX on a suitable GPU host.'}
    try:
        import torch
        from diffusers import FluxPipeline
        pipe=FluxPipeline.from_pretrained('black-forest-labs/FLUX.1-schnell',torch_dtype=torch.bfloat16).to('cuda')
        img=pipe(prompt,num_inference_steps=4,guidance_scale=0.0).images[0]; name=f'{uuid.uuid4()}.png'; img.save(UPLOADS/name)
        return {'status':'completed','media_url':'/media/'+name,'model':'FLUX.1-schnell'}
    except ImportError: raise HTTPException(503,'Install requirements-image.txt on a supported GPU host.')
    except Exception as e: raise HTTPException(503,f'Image generation failed: {e}')
async def transcribe(file:UploadFile):
    if settings.asr_provider!='whisper': return {'status':'demo','transcript':'Transcription demo. Configure Whisper to enable local transcription.'}
    try:
        import whisper
        name=f'{uuid.uuid4()}_{Path(file.filename or "audio.wav").name}'; path=UPLOADS/name; path.write_bytes(await file.read())
        model=whisper.load_model(settings.whisper_model); result=model.transcribe(str(path)); path.unlink(missing_ok=True)
        return {'status':'completed','transcript':result.get('text',''),'model':'Whisper'}
    except ImportError: raise HTTPException(503,'Install requirements-audio.txt to enable Whisper.')
    except Exception as e: raise HTTPException(503,f'Whisper failed: {e}')
