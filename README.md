# AfriVoiceAI

AfriVoiceAI is an early-stage creative workspace for African creators. It combines a React/Vite web app, a FastAPI API, MongoDB Atlas persistence, and replaceable text, speech, image, and transcription adapters.

> **Status:** MVP, not production-certified. Text, speech, image, and transcription default to demo behavior. Hosted text supports direct Google Gemini API and optional Vercel AI Gateway modes; the Render blueprint selects Gemini, which requires a Google AI Studio API key. The production API and Vercel frontend have been deployed; the Vercel site currently requires team login.

## What is implemented

| Area | Current implementation |
| --- | --- |
| Web client | React, TypeScript, Vite; registration/sign-in, creator workspace, generation form, recent history and monthly usage display |
| API | FastAPI; health check, authentication, generations, usage, feedback and consent endpoints |
| Persistence | MongoDB collections for users, generations and feedback; unique email and history indexes |
| Authentication | Email/password, Argon2 password hashing, JWT bearer tokens and email-based password reset; the web client stores the token in browser `localStorage` |
| Usage limit | Monthly per-user generation counter, default 30 |
| Text | Demo by default; optional Ollama local adapter; direct Google Gemini and optional Vercel AI Gateway adapters |
| Speech | Frontend reports that voice generation is in progress; optional Kokoro adapter is not surfaced in the UI yet |
| Transcription | Demo by default; optional Whisper adapter |
| Images | Frontend reports that image generation is in progress; optional FLUX.1-schnell adapter is not surfaced in the UI yet |
| Uploads | Local `uploads` directory mounted at `/media`; not durable production object storage |

Language names in the UI express product intent, not validated model capability. Nigerian English, Pidgin, Yorùbá, Igbo and Hausa require native-speaker evaluation before they can be advertised as supported.

## Architecture

```text
React/Vite browser
        │ HTTPS (VITE_API_URL, bearer token)
        ▼
FastAPI on Render ───── MongoDB Atlas
        │
        ├── Text: demo / Ollama / Google Gemini / optional AI Gateway
        ├── Speech: demo / optional Kokoro
        ├── Transcription: demo / optional Whisper
        └── Images: demo / optional FLUX adapter
```

The browser never receives an AI provider key. The API owns model credentials and calls providers server-side.

## Local development

### Prerequisites

- Docker Desktop with Docker Compose, or compatible Docker Engine and Compose.
- A modern browser.
- No local model installation is required for the default demo.

### Start the MVP

From the repository root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Then open:

- Frontend: <http://localhost:5173>
- API health: <http://localhost:8000/health>
- Interactive API docs: <http://localhost:8000/docs>

The default `.env.example` is intended for Docker Compose. Change `JWT_SECRET` before using real accounts. Keep `.env` private; it is ignored by Git.

### Model modes and local storage

`docker compose up` starts demo behavior; it does not download model weights. Keep this mode if local disk, memory, or GPU is limited.

| Mode | Configuration | Local model storage |
| --- | --- | --- |
| Demo | `AI_MODE=demo` | None |
| Google Gemini free tier | `AI_MODE=gemini`, `GOOGLE_GENERATIVE_AI_API_KEY`, `GEMINI_MODEL=gemini-3.5-flash-lite` | None; free-tier quotas apply |
| Vercel AI Gateway | `AI_MODE=gateway`, `AI_GATEWAY_API_KEY`, `AI_GATEWAY_MODEL` | None; account verification or paid usage may apply |
| Local text | `AI_MODE=local`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Ollama weights are downloaded locally |

For a no-card hosted option, create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey), keep it server-side as `GOOGLE_GENERATIVE_AI_API_KEY`, and set `AI_MODE=gemini`. The current `gemini-3.5-flash-lite` free tier has usage limits; Google states free-tier content may be used to improve its products. Do not send sensitive or customer-confidential content through that tier. The provider may require project verification depending on region or account.

The optional Vercel AI Gateway adapter requires a Gateway key and an accessible model. Do not paste provider keys into chat, frontend variables, source files, or Git.

The direct-provider AI SDK example can be run locally after adding a Google API key to `frontend/.env.local`:

```powershell
Push-Location frontend
npm run gemini:example
Pop-Location
```

For local Ollama testing, use the optional Compose profile:

```powershell
docker compose --profile local-ai up --build
docker compose exec ollama ollama pull llama3.2:3b
```

Set `AI_MODE=local` in `.env` and restart the API to use the downloaded model. **The model pull uses local disk space**; check the current model size and available storage before downloading. Ollama data persists in the `ollama_data` Docker volume.

### Optional speech, image and transcription adapters

These are not part of the default backend requirements and may require large downloads, native system packages, or a suitable GPU:

- Speech: `backend/requirements-audio.txt`; set `TTS_PROVIDER=kokoro`. The current adapter only accepts `en` and `en-NG`.
- Transcription: `backend/requirements-audio.txt`; set `ASR_PROVIDER=whisper` and choose `WHISPER_MODEL`.
- Images: `backend/requirements-image.txt`; set `IMAGE_PROVIDER=flux`. The current FLUX adapter expects CUDA and is not suitable for the deployed free CPU service.

Ask before installing optional dependencies or downloading weights on a resource-limited computer. No African-language speech or transcription quality is claimed without evaluation.

## Configuration

The backend reads environment variables using `backend/app/core/config.py`. `.env.example` documents the local defaults.

| Variable | Purpose | Default / notes |
| --- | --- | --- |
| `ENVIRONMENT` | Deployment environment label | `development` |
| `API_PREFIX` | Versioned API prefix | `/api/v1` |
| `MONGODB_URL` | Mongo connection string | Compose uses `mongodb://mongo:27017`; keep production value secret |
| `MONGODB_DATABASE` | Database name | `afrivoice` |
| `JWT_SECRET` | Signs access tokens | Replace the development placeholder; never expose or commit |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `1440` |
| `FRONTEND_URL` | Frontend base URL used in password reset links | `http://localhost:5173` locally |
| `SMTP_HOST`, `SMTP_PORT` | SMTP server for password reset email | Host required; port defaults to `587` with STARTTLS |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | Optional SMTP login | Set both or leave both empty |
| `SMTP_FROM_EMAIL` | Sender address for password reset email | Required to enable password reset |
| `CORS_ORIGINS` | Comma-separated exact browser origins | `http://localhost:5173` locally |
| `AI_MODE` | Text mode: `demo`, `local`, `gateway` or `gemini` | `demo` locally; Render blueprint uses `gemini` |
| `GOOGLE_GENERATIVE_AI_API_KEY` | Server-side Google AI Studio credential | Required for Gemini mode |
| `GEMINI_MODEL` | Gemini API model ID | `gemini-3.5-flash-lite` |
| `AI_GATEWAY_API_KEY` | Server-side AI Gateway credential | Required only for Gateway mode |
| `AI_GATEWAY_MODEL` | Exact current Gateway model ID | Required only for Gateway mode |
| `OLLAMA_BASE_URL` | Ollama API URL | `http://ollama:11434` in Compose |
| `OLLAMA_MODEL` | Local Ollama model tag | `llama3.2:3b` |
| `TTS_PROVIDER` | Speech adapter | `demo` or optional `kokoro` |
| `ASR_PROVIDER` | Transcription adapter | `demo` or optional `whisper` |
| `WHISPER_MODEL` | Whisper model size/tag | `base` |
| `IMAGE_PROVIDER` | Image adapter | `demo` or optional `flux` |
| `MONTHLY_GENERATION_LIMIT` | Monthly generation allowance | `30` |
| `MAX_UPLOAD_MB` | Maximum audio upload size | `15` |
| `VITE_API_URL` | Frontend API base URL, build-time | `http://localhost:8000/api/v1` for local development |

## API endpoints

Except for health and authentication, endpoints require `Authorization: Bearer <access_token>`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | API and MongoDB connectivity |
| `GET` | `/` | API name and docs link |
| `POST` | `/api/v1/auth/register` | Create account and return a JWT |
| `POST` | `/api/v1/auth/login` | Authenticate and return a JWT |
| `POST` | `/api/v1/auth/forgot-password` | Email a one-hour, single-use password reset link |
| `POST` | `/api/v1/auth/reset-password` | Set a new password using a valid reset token |
| `POST` | `/api/v1/generations` | Generate `text`, `speech` or `image`; persist the result |
| `GET` | `/api/v1/generations` | Return the user's latest 50 generations |
| `GET` | `/api/v1/generations/usage` | Return monthly usage and limit |
| `POST` | `/api/v1/generations/transcribe` | Upload an audio file for transcription |
| `POST` | `/api/v1/feedback` | Submit a rating and optional comment |
| `PUT` | `/api/v1/consent` | Update consent preference fields |

## Current deployment

- **API:** Render web service `afrivoice-api`, rooted at `backend`, pinned to Python `3.11.14`; current health check reports MongoDB connected.
- **Frontend:** Render site `afrivoice-ai-9mzt.onrender.com`, rooted at `frontend`, Vite build; `VITE_API_URL` points to the Render API.
- **Production frontend origin:** `https://afrivoice-ai-9mzt.onrender.com`
- **CORS:** Render `CORS_ORIGINS` must include the exact frontend origin (`https://afrivoice-ai-9mzt.onrender.com`) and any deliberate local/preview origins. The blueprint also retains the prior Vercel origins.
- **Prior Vercel site:** Deployment Protection is enabled; visitors must be authorized team members.
- **Render free instance:** May spin down during inactivity, causing cold-start delays.

For MongoDB Atlas, allow only the backend's current Render outbound ranges and any developer workstation IPs that need access. Render ranges are region-specific and may change; verify them in the Render service's **Connect → Outbound** panel. Do not leave `0.0.0.0/0` enabled after temporary testing.

## Deploy and operate

### Render API

The repository includes `render.yaml` and `.python-version`. The service uses:

```text
Root directory: backend
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Configure `MONGODB_URL`, `JWT_SECRET`, `CORS_ORIGINS` and `GOOGLE_GENERATIVE_AI_API_KEY` in Render's environment settings. To enable password reset, also set `SMTP_HOST`, `SMTP_FROM_EMAIL`, and (when required by the mail provider) both `SMTP_USERNAME` and `SMTP_PASSWORD`; the blueprint sets the production frontend URL and SMTP port. The Render blueprint sets `AI_MODE=gemini` and `GEMINI_MODEL=gemini-3.5-flash-lite`. Keep provider credentials on the server.

### Frontend

Configure the frontend service with project root `frontend`, a Vite build, and set:

```text
VITE_API_URL=https://afrivoice-api.onrender.com/api/v1
```

`VITE_API_URL` is embedded during the Vite build. Redeploy the frontend after changing it. In the Render API service's environment settings, make sure `CORS_ORIGINS` includes the frontend's exact origin (no trailing slash), then redeploy the API. The Render blueprint includes the current frontend origin; existing services may need their environment value updated in the dashboard.

## Security, privacy and limitations

- Never commit `.env`, database connection strings, JWT secrets, or model-provider keys.
- Do not use wildcard CORS for a credentialed API; allow exact origins.
- The current consent schema stores separate platform-use, evaluation and model-training booleans. A complete consent UI, withdrawal flow, retention policy and account deletion are not yet implemented.
- Generation quota is an MVP counter, not a billing system or abuse-prevention rate limiter.
- The browser stores JWTs in `localStorage`; review the authentication design before a public launch.
- Media currently uses local disk and may be lost on redeploy/restart. Use private object storage and signed access for production.
- Admin tools, moderation, payment flows, email verification, background jobs, observability and comprehensive tests are not implemented.
- Do not accept community voice contributions until explicit consent, retention, withdrawal, access control and deletion are implemented.
- Model and dataset licensing, provider data retention, and supported-language claims must be reviewed before commercial use.

See [docs/PRD.md](docs/PRD.md) for product goals, user requirements, acceptance criteria, privacy requirements and the roadmap. [docs/PRODUCT_NOTES.md](docs/PRODUCT_NOTES.md) summarizes current boundaries.

## Model and dependency references

- [Vercel AI Gateway models](https://ai-gateway.vercel.sh/v1/models) and [Gateway API docs](https://vercel.com/docs/ai-gateway)
- [Google AI Studio API keys](https://aistudio.google.com/apikey), [Gemini models](https://aistudio.google.com/docs/models), and [Gemini pricing and data-use terms](https://aistudio.google.com/docs/pricing)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Kokoro-82M model card](https://huggingface.co/hexgrad/Kokoro-82M)
- [Whisper repository](https://github.com/openai/whisper)
- [FLUX.1-schnell model card](https://huggingface.co/black-forest-labs/FLUX.1-schnell)

Review model weights, code, voice assets, datasets and dependency licenses separately. A model license does not demonstrate language quality, dataset consent, or commercial suitability.
