import { StatusDot } from "../../components/ui/StatusDot";
import { Badge } from "../../components/ui/Badge";
import { usePauseJob, useResumeJob, useTriggerJob } from "../../hooks/useJobs";
import type { Job } from "../../types/job";

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
    <div className="rounded border border-border bg-bg-surface p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <StatusDot status={job.last_status} />
          <h3 className="font-medium text-text-primary">{job.name}</h3>
        </div>
        <Badge variant={job.enabled ? "gain" : "neutral"}>{job.enabled ? "enabled" : "paused"}</Badge>
      </div>

      <p className="mt-1 text-xs text-text-muted">{job.description}</p>

      <dl className="mt-3 grid grid-cols-2 gap-2 font-mono text-xs">
        <div>
          <dt className="text-text-faint">Last run</dt>
          <dd className="text-text-primary">{timeAgo(job.last_run_at)}</dd>
        </div>
        <div>
          <dt className="text-text-faint">Duration</dt>
          <dd className="text-text-primary">{job.last_duration_ms ? `${job.last_duration_ms}ms` : "—"}</dd>
        </div>
        <div>
          <dt className="text-text-faint">Success rate</dt>
          <dd className="text-text-primary">{successRate !== null ? `${successRate}%` : "—"}</dd>
        </div>
        <div>
          <dt className="text-text-faint">Failures</dt>
          <dd className={job.failure_count > 0 ? "text-accent-loss" : "text-text-primary"}>
            {job.failure_count}
          </dd>
        </div>
      </dl>

      <div className="mt-4 flex gap-2">
        <button
          onClick={() => trigger.mutate(job.id)}
          disabled={trigger.isPending}
          className="flex-1 rounded border border-border py-1.5 text-xs text-text-primary hover:bg-bg-elevated disabled:opacity-50"
        >
          Run now
        </button>
        {job.enabled ? (
          <button
            onClick={() => pause.mutate(job.id)}
            disabled={pause.isPending}
            className="flex-1 rounded border border-border py-1.5 text-xs text-text-muted hover:bg-bg-elevated disabled:opacity-50"
          >
            Pause
          </button>
        ) : (
          <button
            onClick={() => resume.mutate(job.id)}
            disabled={resume.isPending}
            className="flex-1 rounded border border-accent-gain/40 py-1.5 text-xs text-accent-gain hover:bg-accent-gain/10 disabled:opacity-50"
          >
            Resume
          </button>
        )}
      </div>
    </div>
  );
}