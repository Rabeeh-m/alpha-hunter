import { useContractSecurity, useScanContractSecurity } from "../../hooks/useContractSecurity";
import { Skeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";

function scoreColor(score: number): string {
  if (score >= 70) return "text-accent-gain";
  if (score >= 40) return "text-accent-signal";
  return "text-accent-loss";
}

export function ContractTab({ tokenId }: { tokenId: string }) {
  const { data: security, isLoading } = useContractSecurity(tokenId);
  const scan = useScanContractSecurity(tokenId);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs text-text-muted">
          Automated risk signal from static/dynamic contract analysis — not a guarantee of safety.
        </p>
        <button
          onClick={() => scan.mutate()}
          disabled={scan.isPending}
          className="rounded border border-border px-3 py-1.5 text-xs text-text-primary hover:bg-bg-elevated disabled:opacity-50"
        >
          {scan.isPending ? "Scanning..." : security ? "Re-scan" : "Scan contract"}
        </button>
      </div>

      {isLoading && <Skeleton className="h-40 w-full" />}

      {!isLoading && !security && (
        <EmptyState title="No scan data yet" description="Click 'Scan contract' to run a security check." />
      )}

      {!isLoading && security && (
        <div>
          <div className="mb-4 rounded border border-border bg-bg-surface p-4">
            <p className="text-xs text-text-muted">Safety Score</p>
            <p className={`mt-1 font-mono text-3xl ${scoreColor(security.safety_score)}`}>
              {security.safety_score}
              <span className="text-sm text-text-faint">/100</span>
            </p>
          </div>

          <div className="mb-4 grid grid-cols-3 gap-3 text-xs">
            <div className="rounded border border-border p-3">
              <p className="text-text-muted">Honeypot</p>
              <p className={security.is_honeypot ? "text-accent-loss" : "text-accent-gain"}>
                {security.is_honeypot ? "Yes ⚠" : "No"}
              </p>
            </div>
            <div className="rounded border border-border p-3">
              <p className="text-text-muted">Verified Source</p>
              <p className={security.is_open_source ? "text-accent-gain" : "text-accent-loss"}>
                {security.is_open_source ? "Yes" : "No"}
              </p>
            </div>
            <div className="rounded border border-border p-3">
              <p className="text-text-muted">Buy/Sell Tax</p>
              <p className="font-mono text-text-primary">
                {security.buy_tax ? `${(Number(security.buy_tax) * 100).toFixed(0)}%` : "—"} /{" "}
                {security.sell_tax ? `${(Number(security.sell_tax) * 100).toFixed(0)}%` : "—"}
              </p>
            </div>
          </div>

          <p className="mb-2 text-xs text-text-muted">Flags</p>
          <ul className="space-y-1">
            {security.flags.map((flag, i) => (
              <li key={i} className="rounded border border-border bg-bg-surface px-3 py-2 text-xs text-text-primary">
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
