import { useTokens } from "../hooks/useTokens";

export function DashboardPage() {
  const { data } = useTokens({ page_size: 5 });

  return (
    <div>
      <h1 className="mb-4 text-lg font-semibold text-text-primary">Dashboard</h1>
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded border border-border bg-bg-surface p-4">
          <p className="text-xs text-text-muted">Tokens Tracked</p>
          <p className="mt-1 font-mono text-2xl text-accent-gain">{data?.items.length ?? "—"}</p>        
        </div>
      </div>
      <p className="mt-6 text-sm text-text-muted">
        Full dashboard widgets (trending narratives, alerts feed, whale activity) arrive in later milestones.
      </p>
    </div>
  );
}