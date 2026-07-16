import { useRecentWhaleEvents } from "../hooks/useWhaleEvents";
import { Badge } from "../components/ui/Badge";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";

const EVENT_LABELS: Record<string, { label: string; variant: "gain" | "loss" | "signal" }> = {
  new_position: { label: "New Position", variant: "signal" },
  increased: { label: "Accumulating", variant: "gain" },
  decreased: { label: "Distributing", variant: "loss" },
};

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

function truncate(address: string): string {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

export function WhaleFeedPage() {
  const { data: events, isLoading } = useRecentWhaleEvents(50);

  return (
    <div>
      <h1 className="mb-1 text-lg font-semibold text-text-primary">Whale Activity</h1>
      <p className="mb-4 text-xs text-text-muted">
        Live feed of detected balance changes across your top-ranked tokens (top 10 by Alpha Score, rescanned every ~20min).
      </p>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
        </div>
      )}

      {!isLoading && events?.length === 0 && (
        <EmptyState title="No whale activity detected yet" description="Check back after the next scan cycle, or scan a token manually from its detail page." />
      )}

      {!isLoading && events && events.length > 0 && (
        <div className="space-y-2">
          {events.map((e) => {
            const meta = EVENT_LABELS[e.event_type];
            return (
              <div key={e.id} className="flex items-center justify-between rounded border border-border bg-bg-surface px-4 py-3">
                <div className="flex items-center gap-3">
                  <Badge variant={meta.variant}>{meta.label}</Badge>
                  <div>
                    <p className="font-mono text-sm text-text-primary">
                      {e.token_symbol}
                      <span className="ml-2 text-xs text-text-faint">{e.wallet_label ?? truncate(e.wallet_address)}</span>
                    </p>
                    <p className="text-xs text-text-muted">{timeAgo(e.detected_at)}</p>
                  </div>
                </div>
                <p className="font-mono text-sm text-text-primary">
                  {e.change_usd ? `${Number(e.change_usd) >= 0 ? "+" : ""}$${Math.abs(Number(e.change_usd)).toLocaleString()}` : "—"}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}