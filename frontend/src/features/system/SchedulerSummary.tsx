import { useSchedulerHealth } from "../../hooks/useJobs";
import { StatusDot } from "../../components/ui/StatusDot";
import { Skeleton } from "../../components/ui/Skeleton";

export function SchedulerSummary() {
  const { data, isLoading } = useSchedulerHealth();

  if (isLoading) return <Skeleton className="h-20 w-full" />;

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
    <div className="grid grid-cols-4 gap-4 rounded border border-border bg-bg-surface p-4">
      {stats.map((s) => (
        <div key={s.label}>
          <p className="text-xs text-text-muted">{s.label}</p>
          <p className="mt-1 flex items-center gap-2 font-mono text-lg text-text-primary">
            {s.label === "Status" && <StatusDot status={data?.scheduler_running ? "success" : "failed"} />}
            {s.value}
          </p>
        </div>
      ))}
    </div>
  );
}