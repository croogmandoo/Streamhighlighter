import Link from "next/link";

import { PLANS } from "@/lib/plans";

export default function LandingPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-16">
      <nav className="mb-20 flex items-center justify-between">
        <span className="text-xl font-bold text-brand">StreamHighlighter</span>
        <div className="flex gap-4 text-sm">
          <Link href="/dashboard" className="text-neutral-300 hover:text-white">
            Dashboard
          </Link>
          <Link
            href="/api/auth/signin"
            className="rounded-md bg-brand px-4 py-2 font-medium hover:bg-brand-dark"
          >
            Sign in
          </Link>
        </div>
      </nav>

      <section className="text-center">
        <h1 className="text-balance text-5xl font-extrabold leading-tight">
          Turn long VODs into{" "}
          <span className="text-brand">scroll-stopping shorts</span> — automatically.
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-neutral-300">
          Connect your Twitch or YouTube channel. Our editing agent cuts the dead air,
          finds your funniest moments, and exports ready-to-post Shorts, Reels, and
          TikToks — plus a tightened re-cut of the full stream.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link
            href="/dashboard"
            className="rounded-md bg-brand px-6 py-3 font-semibold hover:bg-brand-dark"
          >
            Start free
          </Link>
          <Link
            href="#pricing"
            className="rounded-md border border-neutral-700 px-6 py-3 font-semibold hover:border-neutral-500"
          >
            See pricing
          </Link>
        </div>
      </section>

      <section className="mt-24 grid gap-6 sm:grid-cols-3">
        {[
          ["1. Connect or upload", "Pull a VOD from Twitch/YouTube or drop a file."],
          ["2. AI edits it", "Dead-air removal + highlight detection across audio, chat, and transcript."],
          ["3. Post everywhere", "Approve clips and auto-publish to Shorts, Reels, and TikTok."],
        ].map(([title, body]) => (
          <div key={title} className="rounded-xl border border-neutral-800 p-6">
            <h3 className="font-semibold">{title}</h3>
            <p className="mt-2 text-sm text-neutral-400">{body}</p>
          </div>
        ))}
      </section>

      <section id="pricing" className="mt-24">
        <h2 className="mb-8 text-center text-3xl font-bold">Pricing</h2>
        <div className="grid gap-6 sm:grid-cols-3">
          {Object.values(PLANS).map((plan) => (
            <div key={plan.id} className="flex flex-col rounded-xl border border-neutral-800 p-6">
              <h3 className="text-lg font-semibold">{plan.name}</h3>
              <p className="mt-2 text-3xl font-bold">
                ${plan.priceMonthly}
                <span className="text-base font-normal text-neutral-400">/mo</span>
              </p>
              <ul className="mt-4 flex-1 space-y-2 text-sm text-neutral-300">
                {plan.features.map((f) => (
                  <li key={f}>• {f}</li>
                ))}
              </ul>
              <Link
                href="/billing"
                className="mt-6 rounded-md bg-brand px-4 py-2 text-center font-medium hover:bg-brand-dark"
              >
                Choose {plan.name}
              </Link>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
