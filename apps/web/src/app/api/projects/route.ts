import { NextResponse } from "next/server";
import { z } from "zod";

import { api } from "@/lib/api";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { quotaFor } from "@/lib/plans";

const Body = z.object({
  source: z.enum(["UPLOAD", "TWITCH", "YOUTUBE"]),
  source_url: z.string().url().optional(),
  title: z.string().optional(),
  weights_preset: z.string().default("balanced"),
});

// POST /api/projects — verify session + quota, then proxy to the pipeline API.
export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const parsed = Body.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }

  // Quota gate: block if the user is over their plan's monthly minutes.
  const sub = await prisma.subscription.findUnique({ where: { userId: session.user.id } });
  const plan = sub?.plan ?? "FREE";
  if (sub && sub.minutesProcessedThisPeriod >= quotaFor(plan)) {
    return NextResponse.json(
      { error: "Monthly processing quota reached. Upgrade your plan." },
      { status: 402 },
    );
  }

  const job = await api.createVod({ user_id: session.user.id, ...parsed.data });
  return NextResponse.json(job, { status: 201 });
}
