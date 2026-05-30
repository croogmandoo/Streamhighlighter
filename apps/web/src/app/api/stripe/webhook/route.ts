import { NextResponse } from "next/server";
import type Stripe from "stripe";

import { prisma } from "@/lib/prisma";
import { type PlanId } from "@/lib/plans";
import { stripe } from "@/lib/stripe";

// Stripe sends raw body; signature must be verified against the unparsed text.
export async function POST(req: Request) {
  const sig = req.headers.get("stripe-signature");
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!sig || !secret) {
    return NextResponse.json({ error: "Missing signature/secret" }, { status: 400 });
  }

  const raw = await req.text();
  let event: Stripe.Event;
  try {
    event = stripe().webhooks.constructEvent(raw, sig, secret);
  } catch (err) {
    return NextResponse.json(
      { error: `Invalid signature: ${err instanceof Error ? err.message : "unknown"}` },
      { status: 400 },
    );
  }

  switch (event.type) {
    case "checkout.session.completed": {
      const s = event.data.object as Stripe.Checkout.Session;
      const userId = s.metadata?.userId;
      const plan = s.metadata?.plan as PlanId | undefined;
      if (userId && plan) {
        await prisma.subscription.upsert({
          where: { userId },
          create: {
            userId,
            plan,
            status: "ACTIVE",
            stripeCustomerId: s.customer as string,
            stripeSubscriptionId: s.subscription as string,
          },
          update: {
            plan,
            status: "ACTIVE",
            stripeSubscriptionId: s.subscription as string,
            minutesProcessedThisPeriod: 0, // reset usage on new period
          },
        });
      }
      break;
    }
    case "customer.subscription.deleted": {
      const s = event.data.object as Stripe.Subscription;
      await prisma.subscription.updateMany({
        where: { stripeSubscriptionId: s.id },
        data: { plan: "FREE", status: "CANCELED" },
      });
      break;
    }
    // TODO(milestone-5): handle invoice.paid (period reset) + payment_failed.
    default:
      break;
  }

  return NextResponse.json({ received: true });
}
