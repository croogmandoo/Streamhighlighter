// Plan definitions: quotas + Stripe price mapping. The marketing page and quota
// checks both read from here so limits never drift between UI and enforcement.

export type PlanId = "FREE" | "STARTER" | "PRO";

export interface PlanDef {
  id: PlanId;
  name: string;
  priceMonthly: number; // USD
  monthlyMinutes: number; // processed-VOD minutes per period
  stripePriceEnv?: string; // env var holding the Stripe price id
  features: string[];
}

export const PLANS: Record<PlanId, PlanDef> = {
  FREE: {
    id: "FREE",
    name: "Free",
    priceMonthly: 0,
    monthlyMinutes: 60,
    features: ["1 connected channel", "60 min/mo", "Watermarked exports"],
  },
  STARTER: {
    id: "STARTER",
    name: "Starter",
    priceMonthly: 19,
    monthlyMinutes: 600,
    stripePriceEnv: "STRIPE_PRICE_STARTER",
    features: ["3 connected channels", "10 hrs/mo", "No watermark", "Auto-publish to 1 platform"],
  },
  PRO: {
    id: "PRO",
    name: "Pro",
    priceMonthly: 49,
    monthlyMinutes: 3000,
    stripePriceEnv: "STRIPE_PRICE_PRO",
    features: [
      "Unlimited channels",
      "50 hrs/mo",
      "No watermark",
      "Auto-publish everywhere",
      "Custom highlight presets",
    ],
  },
};

export function quotaFor(plan: PlanId): number {
  return PLANS[plan].monthlyMinutes;
}
