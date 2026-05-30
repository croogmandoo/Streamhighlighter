import { NextResponse } from "next/server";

import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { PLANS, type PlanId } from "@/lib/plans";
import { stripe } from "@/lib/stripe";

// POST /api/billing/checkout — create a Stripe Checkout session for a plan.
export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const form = await req.formData();
  const planId = String(form.get("plan")) as PlanId;
  const plan = PLANS[planId];
  if (!plan?.stripePriceEnv) {
    return NextResponse.json({ error: "Invalid plan" }, { status: 400 });
  }
  const priceId = process.env[plan.stripePriceEnv];
  if (!priceId) {
    return NextResponse.json({ error: "Plan price not configured" }, { status: 500 });
  }

  // Reuse or create the Stripe customer for this user.
  const sub = await prisma.subscription.findUnique({ where: { userId: session.user.id } });
  let customerId = sub?.stripeCustomerId ?? undefined;
  if (!customerId) {
    const customer = await stripe().customers.create({
      email: session.user.email ?? undefined,
      metadata: { userId: session.user.id },
    });
    customerId = customer.id;
    await prisma.subscription.upsert({
      where: { userId: session.user.id },
      create: { userId: session.user.id, stripeCustomerId: customerId },
      update: { stripeCustomerId: customerId },
    });
  }

  const origin = process.env.NEXTAUTH_URL ?? "http://localhost:3000";
  const checkout = await stripe().checkout.sessions.create({
    mode: "subscription",
    customer: customerId,
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${origin}/billing?status=success`,
    cancel_url: `${origin}/billing?status=cancelled`,
    metadata: { userId: session.user.id, plan: planId },
  });

  return NextResponse.redirect(checkout.url!, { status: 303 });
}
