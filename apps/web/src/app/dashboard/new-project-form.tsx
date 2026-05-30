"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

type Source = "TWITCH" | "YOUTUBE" | "UPLOAD";

export function NewProjectForm() {
  const router = useRouter();
  const [source, setSource] = useState<Source>("TWITCH");
  const [url, setUrl] = useState("");
  const [preset, setPreset] = useState("balanced");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source, source_url: url || undefined, weights_preset: preset }),
      });
      if (!res.ok) throw new Error(await res.text());
      const job = await res.json();
      router.push(`/dashboard/${job.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
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
        <p className="text-sm text-neutral-400">
          {/* TODO(milestone-1): presigned-upload dropzone via /v1/vods/presign-upload */}
          Direct upload coming in the next milestone.
        </p>
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

      {error && <p className="text-sm text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={submitting || source === "UPLOAD"}
        className="rounded-md bg-brand px-4 py-2 font-medium hover:bg-brand-dark disabled:opacity-50"
      >
        {submitting ? "Creating…" : "Create highlights"}
      </button>
    </form>
  );
}
