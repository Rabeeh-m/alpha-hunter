import { useSchedulerHealth } from "../../hooks/useJobs";
import { StatusDot } from "../../components/ui/StatusDot";
import { Skeleton } from "../../components/ui/Skeleton";

export function SchedulerSummary() {
  const { data, isLoading } = useSchedulerHealth();

  if (isLoading) return <Skeleton className="h-24 w-full rounded-xl" />;

  const stats = [
    { label: "Status", value: data?.scheduler_running ? "Running" : "Stopped" },
    { label: "Jobs", value: data?.job_count ?? "—" },
    { label: "Total runs", value: data?.total_executions ?? "—" },
    {
      label: "Success rate",
      value: data?.success_rate !== null && data?.success_rate !== undefined
        ? `${Math.round(data.success_rate * 100)}%`
        : "—",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 rounded-xl border border-border bg-bg-surface p-5 shadow-card lg:grid-cols-4">
      {stats.map((s) => (
        <div key={s.label}>
          <p className="text-xs font-medium tracking-wide text-text-muted uppercase">{s.label}</p>
          <p className="mt-2 flex items-center gap-2 font-mono text-lg font-bold tabular-nums text-text-primary">
            {s.label === "Status" && <StatusDot status={data?.scheduler_running ? "success" : "failed"} />}
            {s.value}
          </p>
        </div>
      ))}
    </div>
  );
}
