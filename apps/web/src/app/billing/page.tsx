import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { PLANS } from "@/lib/plans";

export default async function BillingPage() {
  const session = await auth();
  if (!session?.user) redirect("/api/auth/signin");

  const sub = await prisma.subscription.findUnique({ where: { userId: session.user.id } });
  const currentPlan = sub?.plan ?? "FREE";

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="mb-2 text-2xl font-bold">Billing</h1>
      <p className="mb-8 text-sm text-neutral-400">
        Current plan: <span className="font-semibold text-white">{currentPlan}</span>
        {sub ? ` · ${sub.minutesProcessedThisPeriod} min used this period` : ""}
      </p>

      <div className="grid gap-4 sm:grid-cols-3">
        {Object.values(PLANS).map((plan) => (
          <form key={plan.id} action="/api/billing/checkout" method="POST">
            <input type="hidden" name="plan" value={plan.id} />
            <div className="flex h-full flex-col rounded-xl border border-neutral-800 p-5">
              <h3 className="font-semibold">{plan.name}</h3>
              <p className="mt-1 text-2xl font-bold">${plan.priceMonthly}/mo</p>
              <ul className="mt-3 flex-1 space-y-1 text-xs text-neutral-400">
                {plan.features.map((f) => (
                  <li key={f}>• {f}</li>
                ))}
              </ul>
              <button
                type="submit"
                disabled={plan.id === currentPlan || plan.id === "FREE"}
                className="mt-4 rounded-md bg-brand px-3 py-2 text-sm font-medium hover:bg-brand-dark disabled:opacity-40"
              >
                {plan.id === currentPlan ? "Current" : `Upgrade to ${plan.name}`}
              </button>
            </div>
          </form>
        ))}
      </div>
    </main>
  );
}
