import { useState } from "react";
import { useJobs } from "../hooks/useJobs";
import { SchedulerSummary } from "../features/system/SchedulerSummary";
import { JobCard } from "../features/system/JobCard";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";

export function SystemPage() {
  const { data: jobs, isLoading, isError, error, refetch } = useJobs();
  const [search, setSearch] = useState("");

  const filtered = jobs?.filter((j) => j.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      <h1 className="mb-4 text-lg font-semibold text-text-primary">System</h1>

      <SchedulerSummary />

      <div className="mt-6 mb-3 flex items-center justify-between">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search jobs..."
          className="rounded border border-border bg-bg-elevated px-3 py-1.5 text-sm text-text-primary placeholder:text-text-faint focus:outline-none focus:ring-1 focus:ring-accent-gain"
        />
        <button
          onClick={() => refetch()}
          className="rounded border border-border px-3 py-1.5 text-sm text-text-muted hover:bg-bg-elevated hover:text-text-primary"
        >
          Refresh
        </button>
      </div>

      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {!isError && (
        <div className="grid grid-cols-2 gap-4">
          {isLoading &&
            Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-40 w-full" />)}

          {!isLoading && filtered?.map((job) => <JobCard key={job.id} job={job} />)}
        </div>
      )}

      {!isLoading && !isError && filtered?.length === 0 && (
        <EmptyState title="No jobs found" description="Try a different search term." />
      )}

      <p className="mt-6 text-xs text-text-faint">
        Duration/success-rate history charts require a job-run history endpoint (planned) — not built yet.
      </p>
    </div>
  );
}