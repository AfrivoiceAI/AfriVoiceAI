import logging
import uuid
from pathlib import Path

import httpx
from fastapi import HTTPException, UploadFile
from app.core.config import settings

UPLOADS = Path("uploads")
UPLOADS.mkdir(exist_ok=True)
logger = logging.getLogger(__name__)
AI_GATEWAY_CHAT_COMPLETIONS_URL = "https://ai-gateway.vercel.sh/v1/chat/completions"


async def gateway_text_generate(prompt: str):
    if not settings.ai_gateway_api_key or not settings.ai_gateway_model:
        raise HTTPException(
            status_code=503,
            detail=(
                "Hosted text generation is not configured. Set AI_GATEWAY_API_KEY and "
                "AI_GATEWAY_MODEL, then set AI_MODE=gateway."
            ),
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                AI_GATEWAY_CHAT_COMPLETIONS_URL,
                headers={"Authorization": f"Bearer {settings.ai_gateway_api_key}"},
                json={
                    "model": settings.ai_gateway_model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
    except httpx.TimeoutException:
        logger.exception("AI Gateway request timed out")
        raise HTTPException(504, "The hosted model timed out. Please try again.")
    except httpx.RequestError:
        logger.exception("Unable to reach AI Gateway")
        raise HTTPException(503, "The hosted model service is temporarily unreachable.")

    if response.is_error:
        status_code = response.status_code
        logger.warning("AI Gateway returned HTTP %s", status_code)
        if status_code in (401, 403):
            detail = "AI Gateway authentication or model access failed. Check the server configuration."
        elif status_code == 402:
            detail = "AI Gateway credits or the configured spend budget are unavailable."
        elif status_code == 429:
            detail = "The hosted model is rate limited. Please try again shortly."
        elif status_code >= 500:
            detail = "The hosted model provider is temporarily unavailable."
        else:
            detail = "AI Gateway rejected the request. Check the configured model ID."
        raise HTTPException(503 if status_code != 429 else 429, detail)

    try:
        payload = response.json()
        text = payload["choices"][0]["message"]["content"]
    except (ValueError, KeyError, TypeError, IndexError):
        logger.exception("AI Gateway returned an unexpected response")
        raise HTTPException(502, "The hosted model returned an unexpected response.")

    if not isinstance(text, str) or not text.strip():
        raise HTTPException(502, "The hosted model returned no text.")

    return {"status": "completed", "text": text, "model": settings.ai_gateway_model}


async def text_generate(prompt: str):
    if settings.ai_mode == "demo":
        return {
            "status": "demo",
            "text": (
                f"[Demo output] {prompt}\n\n"
                "Configure a hosted model or enable Ollama to generate live text."
            ),
        }

    if settings.ai_mode == "gateway":
        return await gateway_text_generate(prompt)

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                settings.ollama_base_url.rstrip("/") + "/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.TimeoutException:
        logger.exception("Ollama request timed out")
        raise HTTPException(504, "The local model timed out. Please try again.")
    except httpx.HTTPStatusError as error:
        logger.warning("Ollama returned HTTP %s", error.response.status_code)
        raise HTTPException(503, "Ollama rejected the request. Check its model and endpoint.")
    except httpx.RequestError:
        logger.exception("Unable to reach Ollama")
        raise HTTPException(503, "Ollama is unavailable. Check its service and network address.")

    try:
        text = payload["response"]
    except (KeyError, TypeError):
        logger.exception("Ollama returned an unexpected response")
        raise HTTPException(502, "The local model returned an unexpected response.")

    if not isinstance(text, str) or not text.strip():
        raise HTTPException(502, "The local model returned no text.")

    return {"status": "completed", "text": text, "model": settings.ollama_model}


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
