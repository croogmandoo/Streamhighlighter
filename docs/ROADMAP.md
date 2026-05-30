# Roadmap

This scaffold establishes structure and contracts. Below is the build order to a
shippable v1, and what's stubbed today.

## Milestone 0 — Scaffold (this PR)
- [x] Monorepo layout, docs, env contract
- [x] Next.js app skeleton: landing, auth, dashboard, billing pages
- [x] Prisma schema (identity + billing + connected channels)
- [x] FastAPI app skeleton: routers, SQLAlchemy models, Alembic config
- [x] Celery worker + Redis wiring, pipeline state machine
- [x] Four signal extractors as registered stubs + fusion/selection scaffolding
- [x] docker-compose for Postgres + Redis + services

## Milestone 1 — Ingest + transcribe (real)
- [ ] Presigned upload flow end-to-end
- [ ] `yt-dlp` + Twitch/YouTube VOD pull
- [ ] Twitch chat replay download
- [ ] `faster-whisper` transcription with caching

## Milestone 2 — Real signals + selection
- [ ] Implement silence, audio-energy/laughter, chat-velocity, LLM-humor extractors
- [ ] Tune fusion weights; add user presets
- [ ] Sentence/silence-aware boundary snapping
- [ ] 9:16 reframing (speaker/cam tracking)

## Milestone 3 — Render + review UI
- [ ] ffmpeg render with burned captions
- [ ] Clip review/editor UI (trim, reorder, approve)

## Milestone 4 — Publishing
- [ ] YouTube resumable upload (Shorts + re-cut)
- [ ] TikTok Content Posting API
- [ ] Instagram Reels Graph API

## Milestone 5 — Billing & launch
- [ ] Stripe Checkout + customer portal + webhooks (stubs → real)
- [ ] Quota enforcement and usage metering
- [ ] Onboarding, marketing site polish

## Known integration boundaries (search for `# TODO`)
- Whisper backend, ffmpeg commands, yt-dlp invocation
- Anthropic scoring prompts
- Stripe + NextAuth provider secrets
- Platform publish APIs
