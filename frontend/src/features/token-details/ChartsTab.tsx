import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useTokenSnapshots } from "../../hooks/useTokenDetail";
import { Skeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";

export function ChartsTab({ tokenId }: { tokenId: string }) {
  const { data: snapshots, isLoading } = useTokenSnapshots(tokenId, 24);

  if (isLoading) return <Skeleton className="h-64 w-full rounded-xl" />;

  if (!snapshots || snapshots.length < 2) {
    return (
      <EmptyState
        title="Not enough history yet"
        description="Charts need at least two snapshots — check back after the next refresh cycle."
      />
    );
  }

  const chartData = snapshots.map((s) => ({
    time: new Date(s.captured_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    price: s.price_usd ? Number(s.price_usd) : null,
    liquidity: s.liquidity_usd ? Number(s.liquidity_usd) : null,
  }));

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-bg-surface p-5 shadow-card">
        <p className="mb-4 text-xs font-medium tracking-wide text-text-muted uppercase">Price (24h)</p>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
            <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={11} tickMargin={8} />
            <YAxis stroke="var(--text-muted)" fontSize={11} domain={["auto", "auto"]} tickMargin={8} />
            <Tooltip
              contentStyle={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-default)",
                borderRadius: "12px",
                fontSize: 12,
                boxShadow: "0 10px 35px rgba(15,23,42,.08)",
              }}
            />
            <Line type="monotone" dataKey="price" stroke="var(--brand-success)" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="rounded-xl border border-border bg-bg-surface p-5 shadow-card">
        <p className="mb-4 text-xs font-medium tracking-wide text-text-muted uppercase">Liquidity (24h)</p>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
            <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={11} tickMargin={8} />
            <YAxis stroke="var(--text-muted)" fontSize={11} tickMargin={8} />
            <Tooltip
              contentStyle={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-default)",
                borderRadius: "12px",
                fontSize: 12,
                boxShadow: "0 10px 35px rgba(15,23,42,.08)",
              }}
            />
            <Line type="monotone" dataKey="liquidity" stroke="var(--brand-info)" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
