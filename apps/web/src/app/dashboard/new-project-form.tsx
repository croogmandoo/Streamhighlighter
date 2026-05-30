"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

type Source = "TWITCH" | "YOUTUBE" | "UPLOAD";

export function NewProjectForm() {
  const router = useRouter();
  const [source, setSource] = useState<Source>("TWITCH");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preset, setPreset] = useState("balanced");
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // For UPLOAD: presign → PUT the file directly to storage → return its key.
  async function uploadFile(f: File): Promise<string> {
    setStatus("Requesting upload URL…");
    const presignRes = await fetch("/api/uploads/presign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: f.name, content_type: f.type || "video/mp4" }),
    });
    if (!presignRes.ok) throw new Error(await presignRes.text());
    const { upload_url, storage_key } = await presignRes.json();

    setStatus("Uploading file…");
    const put = await fetch(upload_url, {
      method: "PUT",
      headers: { "Content-Type": f.type || "video/mp4" },
      body: f,
    });
    if (!put.ok) throw new Error(`Upload failed (${put.status})`);
    return storage_key;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      let storageKey: string | undefined;
      if (source === "UPLOAD") {
        if (!file) throw new Error("Choose a file to upload");
        storageKey = await uploadFile(file);
      }

      setStatus("Creating project…");
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source,
          source_url: source === "UPLOAD" ? undefined : url || undefined,
          storage_key: storageKey,
          weights_preset: preset,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const job = await res.json();
      router.push(`/dashboard/${job.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
      setStatus(null);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="flex gap-2">
        {(["TWITCH", "YOUTUBE", "UPLOAD"] as Source[]).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setSource(s)}
            className={`rounded-md px-3 py-1.5 text-sm ${
              source === s ? "bg-brand" : "border border-neutral-700"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {source !== "UPLOAD" ? (
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder={
            source === "TWITCH"
              ? "https://www.twitch.tv/videos/123456789"
              : "https://www.youtube.com/watch?v=..."
          }
          className="w-full rounded-md border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm"
        />
      ) : (
        <input
          type="file"
          accept="video/*"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="w-full rounded-md border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-brand file:px-3 file:py-1 file:text-white"
        />
      )}

      <label className="block text-sm">
        Highlight preset
        <select
          value={preset}
          onChange={(e) => setPreset(e.target.value)}
          className="mt-1 w-full rounded-md border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm"
        >
          <option value="balanced">Balanced</option>
          <option value="chaos">Chaos (chat + energy)</option>
          <option value="storytime">Storytime (narrative)</option>
        </select>
      </label>

      {status && <p className="text-sm text-neutral-400">{status}</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-brand px-4 py-2 font-medium hover:bg-brand-dark disabled:opacity-50"
      >
        {submitting ? "Working…" : "Create highlights"}
      </button>
    </form>
  );
}
