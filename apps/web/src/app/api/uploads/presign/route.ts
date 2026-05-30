import { NextResponse } from "next/server";
import { z } from "zod";

import { api } from "@/lib/api";
import { auth } from "@/lib/auth";

const Body = z.object({
  filename: z.string().min(1),
  content_type: z.string().default("video/mp4"),
});

// POST /api/uploads/presign — mint a presigned PUT URL (proxied to the pipeline
// API). The browser uploads the file directly to object storage, then calls
// /api/projects with the returned storage_key.
export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const parsed = Body.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }

  const result = await api.presignUpload({ user_id: session.user.id, ...parsed.data });
  return NextResponse.json(result);
}
