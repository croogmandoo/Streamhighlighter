"use client";

import { useEffect, useState } from "react";

interface Clip {
  id: string;
  kind: "SHORT" | "RECUT";
  t_start: number;
  t_end: number;
  title: string | null;
  score: number;
  status: string;
}

interface Job {
  id: string;
  stage: string;
  progress: number;
  error: string | null;
  clips: Clip[];
}

const TERMINAL = new Set(["READY", "FAILED"]);

export function JobView({ jobId }: { jobId: string }) {
  const [job, setJob] = useState<Job | null>(null);

  useEffect(() => {
    let active = true;
    const poll = async () => {
      const res = await fetch(`/api/projects/${jobId}`, { cache: "no-store" });
      if (!res.ok) return;
      const data = (await res.json()) as Job;
      if (!active) return;
      setJob(data);
      if (!TERMINAL.has(data.stage)) setTimeout(poll, 2000);
    };
    poll();
    return () => {
      active = false;
    };
  }, [jobId]);

  if (!job) return <p className="text-neutral-400">Loading…</p>;

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-1 flex justify-between text-sm">
          <span>{job.stage}</span>
          <span>{Math.round(job.progress * 100)}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-neutral-800">
          <div
            className="h-full bg-brand transition-all"
            style={{ width: `${Math.round(job.progress * 100)}%` }}
          />
        </div>
      </div>

      {job.error && <p className="text-sm text-red-400">{job.error}</p>}

      {job.clips.length > 0 && (
        <div>
          <h2 className="mb-3 text-lg font-semibold">Clips</h2>
          <ul className="space-y-2">
            {job.clips.map((c) => (
              <li
                key={c.id}
                className="flex items-center justify-between rounded-md border border-neutral-800 px-4 py-2 text-sm"
              >
                <span>
                  <span className="mr-2 rounded bg-neutral-800 px-2 py-0.5 text-xs">{c.kind}</span>
                  {c.title ?? `${c.t_start.toFixed(0)}s – ${c.t_end.toFixed(0)}s`}
                </span>
                <span className="text-neutral-400">score {c.score.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
