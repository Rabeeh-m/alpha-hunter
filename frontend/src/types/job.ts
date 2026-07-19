export type JobStatus = "success" | "failed" | "partial" | null;

export interface Job {
  id: string;
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  interval_seconds: number;
  execution_count: number;
  success_count: number;
  failure_count: number;
  last_run_at: string | null;
  last_duration_ms: number | null;
  last_status: JobStatus;
  next_run_at: string | null;
}

export interface SchedulerHealth {
  scheduler_running: boolean;
  job_count: number;
  total_executions: number;
  success_rate: number | null;
}
