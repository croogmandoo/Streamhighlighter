import { NextResponse } from "next/server";

import { api } from "@/lib/api";
import { auth } from "@/lib/auth";

// GET /api/projects/:id — proxy job status (the browser polls this or uses SSE).
export async function GET(_req: Request, { params }: { params: { id: string } }) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const job = await api.getJob(params.id);
  // Defense in depth: ensure the job belongs to the caller.
  if (job.user_id && job.user_id !== session.user.id) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }
  return NextResponse.json(job);
}
