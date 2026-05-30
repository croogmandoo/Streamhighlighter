import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";
import { NewProjectForm } from "./new-project-form";

export default async function DashboardPage() {
  const session = await auth();
  if (!session?.user) redirect("/api/auth/signin");

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <header className="mb-10 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <span className="text-sm text-neutral-400">{session.user.email}</span>
      </header>

      <section className="rounded-xl border border-neutral-800 p-6">
        <h2 className="mb-4 text-lg font-semibold">New project</h2>
        <NewProjectForm />
      </section>

      <section className="mt-10">
        <h2 className="mb-4 text-lg font-semibold">Recent projects</h2>
        {/* TODO(milestone-1): list the user's vods/jobs from the API with live
            progress via the SSE feed (/v1/jobs/:id/events). */}
        <p className="text-sm text-neutral-500">No projects yet.</p>
      </section>
    </main>
  );
}
