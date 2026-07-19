import type { AlphaFactorBreakdown } from "../../types/tokens";

const LABELS: Record<string, string> = {
  liquidity: "Liquidity", volume: "24H Volume", market_cap: "Market Cap",
  age: "Freshness", liquidity_growth: "Liquidity Growth",
  contract_safety: "Contract Safety", social_signal: "Social Signal", developer_activity: "Developer Activity",
};

function barColor(score: number): string {
  if (score >= 70) return "bg-accent-gain";
  if (score >= 40) return "bg-accent-signal";
  return "bg-accent-loss";
}

export function AlphaBreakdownPanel({ breakdown }: { breakdown: AlphaFactorBreakdown }) {
  const factors = Object.entries(breakdown).filter(([key]) => key !== "composite") as [
    string, { score: number; weight: number },
  ][];

  return (
    <div className="rounded border border-border bg-bg-surface p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-text-muted">Alpha Score</p>
        <p className="font-mono text-2xl text-accent-gain">{breakdown.composite.toFixed(1)}</p>
      </div>
      <div className="space-y-2">
        {factors.map(([key, { score, weight }]) => (
          <div key={key}>
            <div className="flex justify-between text-xs text-text-muted mb-1">
              <span>{LABELS[key] ?? key}</span>
              <span className="font-mono">{score.toFixed(1)} · {(weight * 100).toFixed(0)}% weight</span>
            </div>
            <div className="h-1.5 rounded-full bg-bg-elevated">
              <div className={`h-1.5 rounded-full ${barColor(score)}`} style={{ width: `${score}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}