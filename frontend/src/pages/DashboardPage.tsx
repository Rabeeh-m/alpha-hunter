import { useTokens } from "../hooks/useTokens";

export function DashboardPage() {
  const { data } = useTokens({ page_size: 5 });

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Dashboard</h1>
        <p className="mt-1 text-sm text-text-secondary">Overview of your tracked tokens</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl border border-border bg-bg-surface p-5 shadow-card transition-all hover:shadow-card-hover">
          <p className="text-xs font-medium tracking-wide text-text-muted uppercase">Tokens Tracked</p>
          <p className="mt-2 font-mono text-3xl font-bold text-brand-primary">{data?.items.length ?? "—"}</p>
        </div>
      </div>
      <p className="mt-6 text-sm text-text-muted">
        Full dashboard widgets (trending narratives, alerts feed, whale activity) arrive in later milestones.
      </p>
    </div>
  );
}
