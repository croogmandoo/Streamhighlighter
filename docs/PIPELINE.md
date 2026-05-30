# Editing Pipeline

The pipeline is a state machine driven by Celery. Each `job` advances through
stages; each stage is idempotent and records a `pipeline_event`.

```
INGEST → EXTRACT_AUDIO → TRANSCRIBE → SIGNALS → SCORE → SELECT → RENDER → READY
                                                                      │
                                                              (user reviews)
                                                                      │
                                                                  PUBLISH
```

## Stages

### 1. INGEST  (`pipeline/ingest.py`)
Obtain the source media into object storage.
- `upload`  — user already PUT the file via a presigned URL.
- `twitch`  — pull the VOD via Twitch API + `yt-dlp`.
- `youtube` — pull via YouTube Data API + `yt-dlp`.
Also pulls **Twitch chat replay** (comments) when available, for the chat-velocity
signal.

### 2. EXTRACT_AUDIO  (`pipeline/audio.py`)
`ffmpeg` → 16 kHz mono WAV for transcription + a full-res copy for energy analysis.

### 3. TRANSCRIBE  (`pipeline/transcribe.py`)
`faster-whisper` (local, GPU) or OpenAI Whisper API → word-level timestamps and
segments. Cached by content hash so re-runs are free.

### 4. SIGNALS  (`pipeline/signals/`)
Four independent signal extractors, each producing a time series of scores over
the VOD timeline. They run in parallel.

| Signal              | Module                | What it measures                                  |
|---------------------|-----------------------|---------------------------------------------------|
| Silence / dead air  | `silence.py`          | RMS below threshold for > N seconds → cut candidate |
| Audio energy/laughter | `audio_energy.py`   | Loudness spikes, laughter classifier, speech-rate |
| Chat velocity       | `chat_velocity.py`    | Messages/sec, emote bursts, "LUL"/"OMEGALUL" spikes |
| Transcript + LLM    | `llm_humor.py`        | Claude scores transcript windows for humor/payoff |

Each extractor returns `list[SignalPoint]` where a point is
`(t_start, t_end, score ∈ [0,1], meta)`. Extractors implement a common
`SignalExtractor` protocol so new signals drop in without touching the combiner.

### 5. SCORE  (`pipeline/highlight.py`)
Combine the per-signal time series into a single **highlight curve** over the
timeline via a weighted, normalized fusion. Weights are configurable per user
preset (e.g. "more chaos" weights chat+energy higher; "storytime" weights LLM
narrative payoff). Dead-air segments are inverted (high silence → low keep score).

### 6. SELECT  (`pipeline/select.py`)
Two outputs from the highlight curve:
- **Shorts**: pick the top non-overlapping peaks, snap boundaries to sentence/
  silence edges, target 15–60 s, vertical 9:16 crop around the active speaker/cam.
- **Re-cut VOD**: remove dead air + lowest-scoring stretches while preserving
  narrative continuity; keep 16:9.

### 7. RENDER  (`pipeline/render.py`)
`ffmpeg` cut lists → MP4s. Shorts get 9:16 reframing, optional auto-captions
(burned from the transcript), and intro/outro hooks. Outputs land in object
storage; `clips` rows are created.

### 8. PUBLISH  (`pipeline/publish.py`)
After user review/approval, upload to connected accounts:
- YouTube (Shorts + full re-cut) via YouTube Data API resumable upload.
- TikTok via Content Posting API.
- Instagram Reels via Graph API.
Each target is a `publish_target` with its own status so partial failures retry.

## Extending signals

Add a module under `signals/` implementing `SignalExtractor`, register it in
`signals/__init__.py:REGISTRY`, and give it a default weight in
`highlight.py:DEFAULT_WEIGHTS`. The combiner and selector need no changes.
