# AfriVoiceAI Product Requirements Document

**Version:** 1.0  
**Status:** MVP baseline and proposed product requirements  
**Date:** 25 November 2026  
**Product:** AfriVoiceAI  
**Owner:** AfriVoiceAI

## 1. Product summary

AfriVoiceAI is a browser-based creative workspace intended to help African creators draft and explore digital content using text, voice and image tools. The product should make AI creation approachable while being honest about model limitations, language quality, data use and costs.

The current application is an MVP, not a production-ready generative platform. It has a React/Vite client, FastAPI service, MongoDB persistence and modular model adapters. Demo mode is the default. The hosted text adapter can call Vercel AI Gateway when the service is explicitly configured; speech, transcription and image features remain demo or optional local adapters.

## 2. Problem and opportunity

Creators may face limited access to affordable creative tools, interfaces optimized for other markets, and weak support for local languages and voice styles. A single workspace can reduce tool switching and create a path to evaluate culturally and linguistically appropriate AI workflows.

The opportunity is not to claim that a model already understands every African language or dialect. It is to build a useful creative product, measure real-world quality with local communities, and improve coverage with consented data and transparent evaluation.

## 3. Vision and product principles

**Vision:** Make practical AI-assisted creation accessible to African creators, without requiring local model downloads or overstating language capability.

Principles:

1. **Creator-first:** Start with simple, understandable creation flows.
2. **Language honesty:** Label experimental and unsupported languages clearly.
3. **Privacy by design:** Keep provider keys server-side; collect only necessary data.
4. **Consent before contribution:** Never treat use of the product as consent to train models.
5. **Cost transparency:** Make model choice, usage limits and paid provider dependencies explicit.
6. **Low-resource friendly:** Prefer hosted inference for users with limited storage, memory or GPU access.
7. **Human review:** Treat generated content as a draft that may require factual, cultural and linguistic review.

## 4. Target users

### Primary personas

- **Independent creator:** Produces social, marketing or educational content and wants a fast drafting assistant.
- **Small-business owner:** Needs accessible promotional copy and creative assets without a specialist team.
- **Community educator or storyteller:** Wants to explore content in local languages, with explicit awareness that model quality is still being evaluated.

### Secondary personas

- **Language evaluator:** Reviews model outputs and records structured quality feedback.
- **Product administrator:** Monitors usage, model health, cost, abuse and user requests.

Personas are hypotheses to validate through interviews and usability sessions, not verified market research.

## 5. Goals and non-goals

### MVP goals

- Provide a reliable sign-up/sign-in flow and authenticated creator workspace.
- Let an account request text, speech or image generation and view recent activity.
- Offer a transcription entry point for audio uploads.
- Enforce a simple monthly generation allowance.
- Make the current model mode and language limitations understandable.
- Keep cloud deployment independent of local model weights.
- Capture user feedback and consent preferences without implying that incomplete workflows are production-ready.

### Non-goals for the current MVP

- Train or fine-tune foundation models.
- Claim production-quality support for every African language or dialect.
- Provide video generation, payment processing, team collaboration or enterprise administration.
- Store community voice contributions for training.
- Guarantee factual accuracy or publish model output automatically.
- Offer a public service-level agreement or a measured availability guarantee.

## 6. Current implementation baseline

| Capability | Current state |
| --- | --- |
| Web client | React, TypeScript and Vite; registration, sign-in, text/speech/image selectors, generation form, history and usage display |
| API | FastAPI routes for health, authentication, generations, usage, transcription, feedback and consent preferences |
| Database | MongoDB user, generation and feedback records |
| Authentication | Argon2 password hashing and JWT bearer tokens; frontend token stored in `localStorage` |
| Text model | Demo by default; local Ollama adapter; optional AI Gateway Chat Completions adapter |
| Speech | Demo by default; optional Kokoro adapter, restricted by code to English locale tags |
| Transcription | Demo by default; optional Whisper adapter |
| Images | Demo by default; optional FLUX.1-schnell adapter requiring CUDA |
| Usage | Default monthly limit of 20; counter is an MVP quota, not billing or robust rate limiting |
| Media | Local `uploads` directory; not durable production storage |
| Deployment | Vercel frontend and Render API; MongoDB Atlas |
| Access control | Vercel Deployment Protection currently requires authorized team access |

Current deployment verification on 25 November 2026: Render health reports the database connected; the production Vercel origin passes the API CORS preflight. The production app's login form reached the API and received the expected invalid-credentials response during a non-destructive check.

## 7. User journeys

### 7.1 Create an account and begin

1. Visitor opens the application.
2. Visitor enters name, email and password.
3. API validates input, creates a user with password hash and default consent preferences, and returns a JWT.
4. Client stores session information and loads history and usage.
5. User sees the creator studio and the plan's generation allowance.

**Acceptance:** Invalid inputs receive visible validation/API feedback; a valid new account can authenticate; password values are never stored in plaintext.

### 7.2 Generate a text draft

1. User enters a prompt and chooses Text.
2. Client submits an authenticated request to `/api/v1/generations`.
3. API checks the monthly allowance and routes to the configured demo, local or hosted text mode.
4. API persists the result and returns output, model status and usage.
5. Client displays the result and refreshes history/usage.

**Acceptance:** Missing model configuration produces a clear error instead of a misleading success; provider credentials never reach the browser; provider errors are actionable without returning secrets.

### 7.3 Create speech, an image or a transcription

The interface offers these paths, but each must clearly distinguish demo behavior from a real model result. Unsupported language/model combinations must be rejected with a clear explanation.

### 7.4 Recover from a connection failure

1. Client detects missing API configuration or a browser network failure.
2. Client shows a specific message naming the likely API/CORS configuration check, not just “Failed to fetch.”
3. User can retry after the backend is healthy.

## 8. Functional requirements

Priorities: **P0** launch blocker, **P1** core, **P2** future.

| ID | Priority | Requirement | Current state / acceptance |
| --- | --- | --- | --- |
| FR-01 | P0 | Registration and sign-in | Implemented; verify duplicate email, invalid credentials and expired/invalid token handling |
| FR-02 | P0 | Authenticated API calls | Implemented with bearer JWT; future public release needs a reviewed session-storage strategy |
| FR-03 | P0 | API connectivity errors | Client distinguishes missing `VITE_API_URL`, network/CORS failures, non-JSON responses and HTTP error details |
| FR-04 | P1 | Text generation | Demo/local modes exist; Gateway mode requires server-side key and a current model ID |
| FR-05 | P1 | Generation history | Returns latest 50 user-owned records |
| FR-06 | P1 | Usage display and allowance | Displays count and configured limit; define whether failed attempts consume allowance before launch |
| FR-07 | P1 | Speech generation | Demo exists; real provider must declare language coverage and licensing |
| FR-08 | P1 | Image generation | Demo exists; production path must use an external GPU/model API or suitable hosted worker |
| FR-09 | P1 | Audio transcription | Upload validation and demo/local path exist; add format/duration validation and secure temporary storage |
| FR-10 | P1 | Feedback | Rating/comment endpoint exists; add moderation, retention and admin workflow before collecting at scale |
| FR-11 | P0 | Consent preferences | Preference fields and update endpoint exist; add user-facing notice, versioning, withdrawal and audit workflow |
| FR-12 | P0 | Media persistence | Current local disk is not durable; migrate to private object storage with authorized access before production use |
| FR-13 | P1 | Language quality | Add a native-speaker-reviewed benchmark and only label languages supported after acceptance thresholds pass |
| FR-14 | P1 | Model cost controls | Existing quota is basic; add provider spend budgets, rate limiting, request limits and abuse monitoring |
| FR-15 | P2 | Account deletion and export | Not implemented; provide user-accessible lifecycle controls before public launch |

## 9. Brand and design requirements

### Palette

| Token | Hex | Use |
| --- | --- | --- |
| Deep green | `#0B3526` | Authentication background and navigation |
| Forest green | `#104C34` | Hero surfaces and primary identity |
| Action green | `#17613F` | Primary buttons and active controls |
| Gold | `#C39A2E` | Accent, logo mark, focus indicator and highlights |
| Soft gold | `#FBF4DF` | Result and supporting surfaces |
| White | `#FFFFFF` | Cards, fields and high-contrast text |
| Pale canvas | `#F5F8F5` | Page background |

Green carries the primary action and identity; gold is an accent rather than a large body-text color; white provides clean surfaces and contrast. Maintain keyboard focus visibility and sufficient text contrast.

### UI tone

Confident, welcoming and practical. Avoid pan-African clichés, unsupported claims, and imagery that treats the continent as culturally uniform. Use language names with clear “experimental” or “not yet supported” labels.

## 10. AI and model requirements

### Provider architecture

- The API owns model credentials and calls providers server-side.
- Text supports explicit `demo`, `local` and `gateway` modes.
- Demo remains the safe default until a real provider is configured.
- Gateway mode uses OpenAI-compatible Chat Completions at AI Gateway and an exact model ID supplied through `AI_GATEWAY_MODEL`.
- Model IDs must be selected from the current AI Gateway catalog; do not hardcode a time-sensitive model as a permanent product default.
- The key, model ID, cost and retention policy must be set/reviewed by the service owner before enabling live inference.
- Never silently fall back from a configured live provider to demo output.

### Language and safety

- Use representative prompts and native-speaker reviewers for each claimed language/dialect.
- Track output quality, harmful content, bias, hallucination and code-switching.
- Clearly mark outputs as AI-generated drafts.
- Do not use user prompts or voice uploads for training without separate, informed, revocable consent.
- Record provider/model identity and non-sensitive status metadata for support; do not log API keys or raw sensitive prompts.

### Current limitations

The hosted Gateway path covers text only. Speech, image generation and transcription are not yet connected to hosted providers. The optional local adapters are not suitable as a general production strategy on the current free CPU API service.

## 11. Data, privacy and security requirements

### Data currently handled

- User email, display name, password hash, tier, usage count/month, consent booleans and creation date.
- Generation prompt, type, language, output and creation timestamp.
- Feedback rating, comment, user identifier, optional generation identifier and timestamp.
- Temporary/local audio and generated media files.

### Required safeguards

- Keep secrets in Render/Vercel secret settings, never in frontend bundles or Git.
- Use exact CORS origins; do not use wildcard origins with credentials.
- Restrict Atlas network access to current backend egress ranges and required developer IPs; never leave `0.0.0.0/0` after a temporary test.
- Enforce request size, prompt length, upload type and duration limits.
- Add rate limiting, abuse reporting, secure media storage, retention/deletion controls and auditability.
- Publish a privacy notice describing what is stored, provider processing, retention and user rights.
- Review provider terms, model/provider retention and training policy per selected model.
- Do not collect voice samples for training until a separate consent and withdrawal process exists.

## 12. Non-functional requirements and proposed targets

These are targets for measurement, not claims about the present service.

- **Availability:** Establish a monitored target after choosing a production hosting tier; free-tier cold starts are not an availability guarantee.
- **API reliability:** At least 99% successful non-model API requests in a rolling 30-day pilot, excluding documented client errors.
- **Text latency:** Measure p50/p95 by model/provider; set a product target only after a representative baseline.
- **Accessibility:** Keyboard-operable workflows, visible focus, semantic labels, responsive layout and contrast review.
- **Scalability:** Reuse one MongoDB client per API process; introduce background jobs for long-running media operations.
- **Observability:** Track request outcome, latency, model identifier and safe error category; avoid secrets and sensitive prompt logging.
- **Cost:** Per-user allowance plus provider/team budgets; no uncapped generation route in public production.
- **Resilience:** Health endpoint, provider timeout handling, safe retry policy and clear degraded-service UI.

## 13. Success metrics

Pilot metrics to instrument and baseline:

- Registration completion and authentication error rates.
- Percentage of generation requests completed by modality and model.
- p50/p95 generation latency and provider error categories.
- Cost per successful text generation and monthly spend per active user.
- Weekly active creators and repeat generation rate.
- Feedback rating and qualitative usefulness.
- Language-evaluation score per dialect and reviewer agreement.
- Consent choice, withdrawal, deletion and support request completion.

Do not treat high generation volume as a quality or inclusion metric by itself.

## 14. Release plan

### Phase 0 — Stabilize MVP

- Verify API, database connectivity, CORS and deployment configuration.
- Keep demo mode explicit; surface actionable connection/provider errors.
- Publish setup guide, current implementation notes and product requirements.

### Phase 1 — Private pilot

- Configure one hosted text model after owner selection and budget approval.
- Add automated API/client tests, request rate limiting and safe request-size limits.
- Add a privacy notice, consent UI and consent withdrawal.
- Move uploads to private object storage and implement deletion/retention.
- Recruit native-speaker evaluators and publish an internal benchmark.

### Phase 2 — Public beta

- Resolve Vercel access policy intentionally; deployment is currently team-protected.
- Add moderation, monitoring, admin support workflows and account deletion/export.
- Enable public access only after security, privacy, cost and language acceptance criteria pass.
- Add hosted speech/image/transcription providers only after model evaluation and cost review.

### Phase 3 — Scale and improve

- Optimize provider routing based on measured quality, availability, cost and privacy.
- Improve local-language coverage through consented, governed evaluation and data processes.
- Consider collaboration, billing and additional modalities after validating core retention.

## 15. Risks and dependencies

| Risk | Mitigation |
| --- | --- |
| Current providers may not perform well for targeted languages | Native-speaker evaluation; communicate unsupported/experimental status |
| Unbounded provider spend | Keep Gateway opt-in, select model explicitly, establish budgets and enforce quotas |
| Atlas is exposed by broad IP allowlisting | Replace temporary `0.0.0.0/0` with Render egress CIDRs and required developer IPs |
| Free Render instance sleeps or lacks GPU | Use hosted inference and document cold starts; move long tasks to suitable infrastructure |
| Local media disappears after redeploy | Use private object storage and signed URLs |
| Consent fields are mistaken for complete consent management | Add UI, purpose-specific consent, withdrawal and audit trail |
| Users assume demo output is live AI | Label demo status and distinguish it from completed model output |
| Browser-side token storage increases XSS impact | Review cookie/session strategy and strengthen CSP before public launch |

## 16. Open product decisions

- Which initial hosted text model best balances cost, language quality, provider availability and data policy?
- What monthly provider budget and per-user generation allowance are acceptable?
- Which languages/dialects are first-release commitments, and who will evaluate them?
- Should the Vercel production site remain team-protected or become public after readiness review?
- What are the retention, export and deletion periods for prompts, outputs, feedback and audio?
- Which hosted speech, image and transcription providers satisfy cost, licensing and language requirements?

## 17. MVP acceptance checklist

- [ ] A new user can register and sign in; invalid credentials produce a useful response.
- [ ] Frontend reaches the configured API from the allowed production origin.
- [ ] Missing API config, CORS/network errors and API errors have distinct, actionable messages.
- [ ] Demo behavior is clearly identified; no real inference is implied when demo mode is enabled.
- [ ] Hosted text mode requires server-side credentials and a selected current model ID.
- [ ] Provider failures never return success-shaped demo output.
- [ ] The user can see history and monthly usage for their own account.
- [ ] Model/language claims are supported by an evaluation record.
- [ ] Atlas access is restricted; secrets are absent from source and browser bundles.
- [ ] Consent, retention, account deletion and secure media workflows are completed before public launch.
