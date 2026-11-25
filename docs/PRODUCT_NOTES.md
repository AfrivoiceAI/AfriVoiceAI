# AfriVoiceAI product notes

AfriVoiceAI is an early-stage creator workspace. The current implementation includes email/password authentication, a monthly free usage counter, MongoDB generation history, feedback, consent preference fields, and demo/local model adapters. Hosted text generation through AI Gateway is opt-in and requires a server-side key and an explicitly selected current model ID.

Speech (Kokoro), transcription (Whisper) and image generation (FLUX) are optional adapters, not production-ready hosted capabilities. Language quality—especially Nigerian English, Pidgin, Yorùbá, Igbo and Hausa—must be measured with native speakers before support is claimed.

The brand palette is green, gold and white. Detailed requirements, personas, acceptance criteria, privacy expectations and roadmap are in [PRD.md](PRD.md).

Not implemented: video, payments, admin/moderation, email verification, password reset, account deletion, production media storage, background jobs, consent withdrawal, model fine-tuning, robust rate limiting and comprehensive automated tests.

Before public launch: remove any temporary broad database network allowlist, implement consent and deletion workflows, move media to private object storage, validate model-provider costs and retention, run native-speaker evaluations, and add monitoring and security testing.
