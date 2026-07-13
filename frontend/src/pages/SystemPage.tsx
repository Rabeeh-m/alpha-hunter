import { useState } from "react";
import { useJobs } from "../hooks/useJobs";
import { SchedulerSummary } from "../features/system/SchedulerSummary";
import { JobCard } from "../features/system/JobCard";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { RefreshCw, Search } from "lucide-react";

export function SystemPage() {
  const { data: jobs, isLoading, isError, error, refetch } = useJobs();
  const [search, setSearch] = useState("");

  const filtered = jobs?.filter((j) => j.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-text-primary">System</h1>
          <p className="mt-1 text-sm text-text-secondary">Monitor jobs and scheduler health</p>
        </div>
      </div>

      <SchedulerSummary />

      <div className="mt-6 mb-4 flex items-center justify-between gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search jobs..."
            className="w-full rounded-xl border border-border bg-bg-surface py-2.5 pl-9 pr-3 text-sm text-text-primary placeholder:text-text-muted shadow-card transition-all focus:outline-none focus:ring-2 focus:ring-brand-primary/30 focus:border-brand-primary"
          />
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 rounded-xl border border-border bg-bg-surface px-4 py-2.5 text-sm font-medium text-text-secondary shadow-card transition-all hover:bg-bg-hover hover:text-text-primary hover:shadow-card-hover"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {!isError && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {isLoading &&
            Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-48 w-full rounded-xl" />
            ))}

          {!isLoading && filtered?.map((job) => <JobCard key={job.id} job={job} />)}
        </div>
      )}

      {!isLoading && !isError && filtered?.length === 0 && (
        <EmptyState title="No jobs found" description="Try a different search term." />
      )}

      <p className="mt-6 text-xs text-text-muted">
        Duration/success-rate history charts require a job-run history endpoint (planned) — not built yet.
      </p>
    </div>
  );
}
