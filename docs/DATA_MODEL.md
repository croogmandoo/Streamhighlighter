# Data Model

One Postgres database. Web-owned tables are managed by Prisma; API-owned tables by
Alembic. Both reference `users.id`.

## Web-owned (Prisma) — identity & billing

- **User** — `id`, `email`, `name`, `image`, `createdAt`.
- **Account / Session / VerificationToken** — standard NextAuth tables.
- **Subscription** — `id`, `userId`, `stripeCustomerId`, `stripeSubscriptionId`,
  `plan` (`FREE|STARTER|PRO`), `status`, `currentPeriodEnd`, usage counters
  (`minutesProcessedThisPeriod`).
- **ConnectedChannel** — `id`, `userId`, `platform`
  (`TWITCH|YOUTUBE|TIKTOK|INSTAGRAM`), `externalId`, `accessTokenEnc`,
  `refreshTokenEnc`, `scope`, `expiresAt`. Used both for VOD retrieval (Twitch/
  YouTube) and publishing (YouTube/TikTok/Instagram).

## API-owned (SQLAlchemy) — media & processing

- **vods** — `id`, `user_id`, `source` (`UPLOAD|TWITCH|YOUTUBE`), `source_url`,
  `title`, `duration_s`, `storage_key`, `chat_storage_key`, `status`, timestamps.
- **jobs** — `id`, `vod_id`, `user_id`, `stage`
  (`INGEST…READY|PUBLISH|FAILED`), `progress` (0–1), `weights_preset`,
  `error`, timestamps.
- **clips** — `id`, `job_id`, `kind` (`SHORT|RECUT`), `t_start`, `t_end`,
  `storage_key`, `title`, `caption`, `score`, `status`
  (`DRAFT|APPROVED|PUBLISHED`).
- **publish_targets** — `id`, `clip_id`, `platform`, `status`, `external_url`,
  `error`.
- **pipeline_events** — `id`, `job_id`, `stage`, `level`, `message`, `data`,
  `created_at`. Append-only audit/progress log; powers the live SSE feed.

## Quota enforcement

`Subscription.minutesProcessedThisPeriod` is checked by the web tier before a job
is created, and incremented by the API (via an internal callback) once a VOD's
duration is known. Plans cap monthly processed minutes.
