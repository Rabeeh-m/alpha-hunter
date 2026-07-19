import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useNarrativeDistribution } from "../hooks/useNarratives";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";

const COLORS = ["#22D3B8", "#F0B429", "#F0554A", "#5A6479", "#8993A8", "#22D3B8", "#F0B429"];

export function NarrativesPage() {
  const { data: distribution, isLoading } = useNarrativeDistribution();

  const chartData = distribution
    ? Object.entries(distribution).map(([narrative, count]) => ({ narrative: narrative.replace("_", " "), count }))
    : [];

  return (
    <div>
      <h1 className="mb-1 text-lg font-semibold text-text-primary">Narratives</h1>
      <p className="mb-4 text-xs text-text-muted">
        Distribution of classified tokens by category. Classification is a weak-signal heuristic — see individual token confidence scores.
      </p>

      {isLoading && <Skeleton className="h-64 w-full" />}
      {!isLoading && chartData.length === 0 && (
        <EmptyState title="No classifications yet" description="Classify tokens from their detail page, or wait for the scheduled batch job." />
      )}
      {!isLoading && chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#1F2733" />
            <XAxis type="number" stroke="#5A6479" fontSize={11} />
            <YAxis type="category" dataKey="narrative" stroke="#5A6479" fontSize={11} width={100} />
            <Tooltip contentStyle={{ background: "#12161F", border: "1px solid #1F2733", fontSize: 12 }} />
            <Bar dataKey="count">
              {chartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
