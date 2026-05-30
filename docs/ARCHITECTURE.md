# Architecture

## Overview

StreamHighlighter is split into two deployable apps sharing one Postgres DB and a
Redis queue:

| App        | Tech                       | Responsibility                                   |
|------------|----------------------------|--------------------------------------------------|
| `apps/web` | Next.js 14, TS, Tailwind   | Marketing site, dashboard, auth, Stripe billing  |
| `apps/api` | FastAPI, SQLAlchemy, Celery| VOD ingestion, editing pipeline, publishing      |

### Why two languages

- The **web tier** benefits from the Next.js/React ecosystem for a polished
  product UI, NextAuth for social login, and first-class Stripe support.
- The **pipeline tier** needs Python for the ML/video toolchain: `faster-whisper`
  for transcription, `librosa`/`numpy` for audio analysis, `ffmpeg` orchestration,
  and the Anthropic SDK for LLM scoring.

## Data ownership

A single Postgres database, two schemas of ownership:

- **Web owns** (via Prisma): `User`, `Account`, `Session`, `Subscription`,
  `ConnectedChannel` (OAuth tokens for source/publish platforms).
- **API owns** (via SQLAlchemy + Alembic): `vods`, `jobs`, `clips`,
  `pipeline_events`.

Both reference `users.id`. The web app is the source of truth for identity and
billing; the API is the source of truth for media and processing. They never
write each other's tables. The API trusts a signed `X-Internal-Secret` header
(`INTERNAL_API_SECRET`) on requests proxied from the web app, plus the resolved
`user_id`.

See [`docs/DATA_MODEL.md`](DATA_MODEL.md) for the full schema.

## Request flow: "Create a highlight job"

```
1. User clicks "New project" in the dashboard, picks a Twitch VOD URL.
2. web → POST /api/projects (Next.js route handler)
      - verifies NextAuth session
      - checks subscription quota (Subscription.plan, usage this period)
      - proxies → api: POST /v1/vods  { source, url, user_id }   (+ internal secret)
3. api creates a `vods` row (status=PENDING) and a `jobs` row (stage=INGEST),
   enqueues Celery task `run_pipeline(job_id)`, returns job id.
4. Celery worker runs the pipeline state machine (see PIPELINE.md), writing
   `pipeline_events` and updating `jobs.stage` / `jobs.progress` as it goes.
5. web polls GET /api/projects/:id (proxy → GET /v1/jobs/:id) or subscribes to
   SSE /v1/jobs/:id/events for live progress.
6. On completion, `clips` rows point at rendered media in object storage;
   user reviews, edits selection, and clicks Publish.
```

## Queue & workers

- **Broker/result backend:** Redis.
- **Orchestration:** Celery. One logical task per job, `run_pipeline(job_id)`,
  which advances a state machine. Long sub-steps (transcription, rendering) are
  their own tasks so they can be retried and parallelized independently.
- **Concurrency:** GPU-bound steps (Whisper) and CPU/ffmpeg steps are routed to
  separate Celery queues (`gpu`, `render`, `default`) so they scale separately.

## Object storage

All media (source VODs, extracted audio, rendered clips) lives in S3-compatible
storage. The DB stores only keys/URIs, never blobs. Uploads from the browser use
presigned PUT URLs minted by the API.

## Security boundaries

- Browser never talks to the API directly; the Next.js server proxies and injects
  the internal secret + authenticated `user_id`.
- OAuth tokens for connected platforms are encrypted at rest (column-level) and
  only the API decrypts them when publishing.
- Stripe webhooks hit a dedicated Next.js route with signature verification.

## Deployment topology (target)

- `web` → Vercel or a container on the app platform of choice.
- `api` (FastAPI) + `worker` (Celery) → containers (same image, different ent
  command) behind the queue.
- Postgres + Redis → managed services.
- Object storage → S3 / Cloudflare R2.

See [`infra/docker-compose.yml`](../infra/docker-compose.yml) for the local
equivalent.
