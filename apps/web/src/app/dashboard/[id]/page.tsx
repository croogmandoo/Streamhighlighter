import { JobView } from "./job-view";

export default function JobPage({ params }: { params: { id: string } }) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="mb-6 text-2xl font-bold">Processing your VOD</h1>
      <JobView jobId={params.id} />
    </main>
  );
}
