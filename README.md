# StreamHighlighter

> Turn long Twitch/YouTube VODs into publish-ready short-form clips and a tightened
> re-cut VOD — automatically.

StreamHighlighter is a subscription SaaS. A creator connects their Twitch/YouTube
account (or uploads a file), and an AI editing pipeline:

1. **Ingests** the VOD (upload, Twitch VOD pull, or YouTube pull).
2. **Removes dead air** — long silences and low-activity stretches are cut.
3. **Scores moments** for "highlight-worthiness" by combining four signals:
   - Transcript + LLM humor/engagement scoring (Whisper → Claude)
   - Audio energy / laughter detection
   - Twitch chat velocity & emote spikes
   - Silence / dead-air detection
4. **Renders** vertical short-form clips (Shorts / Reels / TikTok) and a tightened
   horizontal re-cut of the full VOD.
5. **Publishes** to YouTube / TikTok / Instagram (OAuth-connected accounts).

## Architecture

This is a monorepo with two deployable apps that share one Postgres database and
a Redis queue.

```
streamhighlighter/
├── apps/
│   ├── web/        Next.js 14 (App Router, TS, Tailwind) — UI, auth, Stripe billing
│   └── api/        FastAPI (Python) — ingestion + editing pipeline + workers
├── packages/
│   └── shared/     Shared TypeScript types / API contract
├── infra/          docker-compose, deployment notes
└── docs/           Architecture & product docs
```

```
        ┌──────────────┐        ┌─────────────────┐
Browser │  Next.js web │  HTTP  │   FastAPI api   │
───────▶│  auth + UI   │───────▶│  REST + webhooks│
        │  Stripe      │        └────────┬────────┘
        └──────┬───────┘                 │ enqueue
               │ NextAuth/Prisma         ▼
               │                 ┌─────────────────┐
               ▼                 │  Redis (queue)  │
        ┌──────────────┐         └────────┬────────┘
        │   Postgres   │◀──SQLAlchemy──┐   │
        │ users/subs/  │               │   ▼
        │ vods/jobs/   │      ┌──────────────────────┐
        │ clips        │◀─────│  Celery worker pool  │
        └──────────────┘      │  ingest→transcribe→  │
                              │  signals→render→pub  │
        ┌──────────────┐      └──────────┬───────────┘
        │ Object store │◀────────────────┘
        │ (S3/R2)      │  media in/out
        └──────────────┘
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design and
[`docs/PIPELINE.md`](docs/PIPELINE.md) for the editing pipeline details.

## Quick start (local dev)

Prereqs: Docker + Docker Compose, Node 20+, Python 3.11+, `ffmpeg`.

```bash
cp .env.example .env        # fill in secrets

# Bring up Postgres + Redis (and optionally web/api/worker)
docker compose -f infra/docker-compose.yml up -d postgres redis

# --- Web ---
cd apps/web
npm install
npx prisma migrate dev      # creates auth/billing tables
npm run dev                 # http://localhost:3000

# --- API + worker (in another shell) ---
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head        # creates pipeline tables
uvicorn app.main:app --reload --port 8000
celery -A app.worker.celery_app worker --loglevel=info
```

## Status

This repository is an **architectural scaffold**. The structure, contracts, DB
schema, queue wiring, and pipeline stages are in place. Stages marked `# TODO`
contain the integration boundaries (Whisper, ffmpeg, Twitch/YouTube/Stripe APIs)
where real implementations plug in. See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## License

Proprietary — © 2026. All rights reserved.
