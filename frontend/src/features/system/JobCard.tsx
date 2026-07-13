import { StatusDot } from "../../components/ui/StatusDot";
import { Badge } from "../../components/ui/Badge";
import { usePauseJob, useResumeJob, useTriggerJob } from "../../hooks/useJobs";
import type { Job } from "../../types/job";
import { Play, Pause, RotateCw } from "lucide-react";

function timeAgo(iso: string | null): string {
  if (!iso) return "never";
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  return `${Math.floor(seconds / 60)}m ago`;
}

export function JobCard({ job }: { job: Job }) {
  const trigger = useTriggerJob();
  const pause = usePauseJob();
  const resume = useResumeJob();

  const successRate = job.execution_count > 0 ? Math.round((job.success_count / job.execution_count) * 100) : null;

  return (
    <div className="rounded-xl border border-border bg-bg-surface p-5 shadow-card transition-all hover:shadow-card-hover hover:border-border">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <StatusDot status={job.last_status} />
          <h3 className="font-semibold text-text-primary">{job.name}</h3>
        </div>
        <Badge variant={job.enabled ? "success" : "neutral"}>{job.enabled ? "enabled" : "paused"}</Badge>
      </div>

      <p className="mt-2 text-sm text-text-secondary">{job.description}</p>

      <dl className="mt-4 grid grid-cols-2 gap-y-3 gap-x-4 font-mono text-xs">
        <div>
          <dt className="text-text-muted">Last run</dt>
          <dd className="mt-0.5 font-medium text-text-primary">{timeAgo(job.last_run_at)}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Duration</dt>
          <dd className="mt-0.5 font-medium text-text-primary">{job.last_duration_ms ? `${job.last_duration_ms}ms` : "—"}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Success rate</dt>
          <dd className="mt-0.5 font-medium text-text-primary">{successRate !== null ? `${successRate}%` : "—"}</dd>
        </div>
        <div>
          <dt className="text-text-muted">Failures</dt>
          <dd className={`mt-0.5 font-medium ${job.failure_count > 0 ? "text-brand-danger" : "text-text-primary"}`}>
            {job.failure_count}
          </dd>
        </div>
      </dl>

      <div className="mt-4 flex gap-2">
        <button
          onClick={() => trigger.mutate(job.id)}
          disabled={trigger.isPending}
          className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-border bg-bg-surface px-3 py-2 text-xs font-medium text-text-secondary shadow-card transition-all hover:bg-bg-hover hover:text-text-primary hover:shadow-card-hover disabled:opacity-50"
        >
          <RotateCw size={12} />
          Run now
        </button>
        {job.enabled ? (
          <button
            onClick={() => pause.mutate(job.id)}
            disabled={pause.isPending}
            className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-border bg-bg-surface px-3 py-2 text-xs font-medium text-text-secondary shadow-card transition-all hover:bg-bg-hover hover:text-text-primary hover:shadow-card-hover disabled:opacity-50"
          >
            <Pause size={12} />
            Pause
          </button>
        ) : (
          <button
            onClick={() => resume.mutate(job.id)}
            disabled={resume.isPending}
            className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-brand-success/30 bg-brand-success-light/50 px-3 py-2 text-xs font-medium text-brand-success shadow-card transition-all hover:bg-brand-success-light hover:shadow-card-hover disabled:opacity-50"
          >
            <Play size={12} />
            Resume
          </button>
        )}
      </div>
    </div>
  );
}
