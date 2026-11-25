# AfriVoice AI MVP
React + TypeScript + Vite frontend, FastAPI backend, MongoDB database. This is a runnable starter, not a production-certified service.

## Run locally
1. Install Docker Desktop.
2. `cp .env.example .env` (Windows: copy `.env.example` to `.env`). Replace `JWT_SECRET` with a long random value.
3. `docker compose up --build`
4. Open frontend http://localhost:5173 and API docs http://localhost:8000/docs.
5. Register a user. Demo mode is enabled by default.

## Enable local open models
Text: install Ollama from https://ollama.com, then run `ollama pull llama3.2:3b`. For Docker, start its profile with `docker compose --profile local-ai up --build`, then `docker compose exec ollama ollama pull llama3.2:3b`. Set `AI_MODE=local` and `OLLAMA_BASE_URL=http://ollama:11434` in `.env`, then restart API.

Speech: `cd backend && pip install -r requirements-audio.txt`; set `TTS_PROVIDER=kokoro` for Kokoro-82M English TTS or `ASR_PROVIDER=whisper` for Whisper transcription. These are optional and may require OS/runtime dependencies. Kokoro's published card lists English voices; it is NOT a validated Nigerian English/Pidgin/Yoruba/Igbo/Hausa model. Whisper performance for African languages must be measured, not assumed.

Image: optional FLUX.1-schnell adapter in `requirements-image.txt`. It is a 12B model and generally needs a suitable GPU; not suitable for a small CPU-only Render instance. Default image mode is demo.

## Deploy
- MongoDB Atlas: create a database/user and allow the backend network; set `MONGODB_URL` and `MONGODB_DATABASE`.
- Render: deploy `render.yaml` or create Python web service with root `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set secrets/env vars.
- Vercel: root `frontend`, build `npm run build`, output `dist`; set `VITE_API_URL=https://YOUR-API/api/v1`.
- Set backend `CORS_ORIGINS` to exact frontend origin. Never commit `.env` or secrets.

## Model/licence references
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- Kokoro-82M model card (Apache-2.0): https://huggingface.co/hexgrad/Kokoro-82M
- Whisper repository (MIT): https://github.com/openai/whisper
- FLUX.1-schnell model card (Apache-2.0): https://huggingface.co/black-forest-labs/FLUX.1-schnell
Review model weights, code, voice assets, datasets and dependency licenses separately before commercial use. Apache licensing does not imply a model supports Nigerian languages.

## MVP scope and gaps
Includes email/password auth, MongoDB users/history/feedback, monthly free quota, text generation, speech/image adapters, transcription upload, and separated consent flags. Does not yet include video, payments, email verification, password reset, admin/moderation, production object storage, background queue, data curation/training pipeline, account deletion or consent withdrawal workflow. Do not collect voice contributions until consent, retention, withdrawal, access control and deletion are implemented. Keep media out of MongoDB for production; use private object storage and signed URLs. Add rate limiting, tests, monitoring and security review before public launch.
