function scoreColor(score: number): string {
  if (score >= 70) return "text-accent-gain";
  if (score >= 40) return "text-accent-signal";
  return "text-accent-loss";
}

export function AlphaScoreBadge({ score }: { score: string | null }) {
  if (score === null) return <span className="text-text-faint">—</span>;
  const n = Number(score);
  return <span className={`font-mono font-medium ${scoreColor(n)}`}>{n.toFixed(1)}</span>;
}