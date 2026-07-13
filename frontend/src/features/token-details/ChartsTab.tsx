import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useTokenSnapshots } from "../../hooks/useTokenDetail";
import { Skeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";

export function ChartsTab({ tokenId }: { tokenId: string }) {
  const { data: snapshots, isLoading } = useTokenSnapshots(tokenId, 24);

  if (isLoading) return <Skeleton className="h-64 w-full" />;

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
      <div>
        <p className="mb-2 text-xs text-text-muted">Price (24h)</p>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1F2733" />
            <XAxis dataKey="time" stroke="#5A6479" fontSize={11} />
            <YAxis stroke="#5A6479" fontSize={11} domain={["auto", "auto"]} />
            <Tooltip contentStyle={{ background: "#12161F", border: "1px solid #1F2733", fontSize: 12 }} />
            <Line type="monotone" dataKey="price" stroke="#22D3B8" dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div>
        <p className="mb-2 text-xs text-text-muted">Liquidity (24h)</p>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1F2733" />
            <XAxis dataKey="time" stroke="#5A6479" fontSize={11} />
            <YAxis stroke="#5A6479" fontSize={11} />
            <Tooltip contentStyle={{ background: "#12161F", border: "1px solid #1F2733", fontSize: 12 }} />
            <Line type="monotone" dataKey="liquidity" stroke="#F0B429" dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}