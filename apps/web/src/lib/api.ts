// Server-only client for the FastAPI pipeline service. The browser NEVER calls
// the API directly; Next.js route handlers proxy and inject the internal secret
// plus the authenticated user id. Importing this in client code is a bug.

import "server-only";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";
const INTERNAL_API_SECRET = process.env.INTERNAL_API_SECRET ?? "change-me";

async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-Internal-Secret": INTERNAL_API_SECRET,
    },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${method} ${path} failed (${res.status}): ${detail}`);
  }
  return (await res.json()) as T;
}

export interface JobRef {
  job_id: string;
  vod_id: string;
  stage: string;
  progress: number;
}

export const api = {
  createVod: (input: {
    user_id: string;
    source: "UPLOAD" | "TWITCH" | "YOUTUBE";
    source_url?: string;
    title?: string;
    weights_preset?: string;
  }) => call<JobRef>("POST", "/v1/vods", input),

  presignUpload: (input: { user_id: string; filename: string; content_type?: string }) =>
    call<{ upload_url: string; storage_key: string }>("POST", "/v1/vods/presign-upload", input),

  getJob: (jobId: string) => call<Record<string, unknown>>("GET", `/v1/jobs/${jobId}`),

  publish: (jobId: string, input: { clip_ids: string[]; platforms: string[] }) =>
    call<{ queued: number }>("POST", `/v1/jobs/${jobId}/publish`, input),
};
