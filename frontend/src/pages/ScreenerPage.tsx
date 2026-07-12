import { useNavigate } from "react-router-dom";
import { useTokens } from "../hooks/useTokens";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { Badge } from "../components/ui/Badge";

const COLUMNS = ["Token", "Chain", "DEX", "Price", "24H Vol", "Liquidity", "FDV", "Mkt Cap", "Alpha"];

function formatUsd(value: string | null): string {
  if (value === null) return "—";
  const n = Number(value);
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

export function ScreenerPage() {
  const { data: tokens, isLoading, isError, error, refetch } = useTokens(50, 0);
  const navigate = useNavigate();

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-text-primary">Token Screener</h1>
        <button
          onClick={() => refetch()}
          className="rounded border border-border px-3 py-1.5 text-sm text-text-muted hover:bg-bg-elevated hover:text-text-primary"
        >
          Refresh
        </button>
      </div>

      {isError && (
        <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
      )}

      {!isError && (
        <div className="overflow-x-auto rounded border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-bg-surface text-left text-xs text-text-muted">
                {COLUMNS.map((col) => (
                  <th key={col} className="px-4 py-2 font-medium">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading &&
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-border">
                    {COLUMNS.map((col) => (
                      <td key={col} className="px-4 py-3"><Skeleton className="h-4 w-16" /></td>
                    ))}
                  </tr>
                ))}

              {!isLoading &&
                tokens?.map((token) => (
                  <tr
                    key={token.id}
                    onClick={() => navigate(`/tokens/${token.id}`)}
                    className="cursor-pointer border-b border-border font-mono text-xs hover:bg-bg-surface"
                  >
                    <td className="px-4 py-3 font-sans font-medium text-text-primary">{token.symbol}</td>
                    <td className="px-4 py-3"><Badge variant="neutral">{token.chain}</Badge></td>
                    <td className="px-4 py-3 text-text-muted">{token.dex ?? "—"}</td>
                    <td className="px-4 py-3 font-tabular">{formatUsd(token.price_usd)}</td>
                    <td className="px-4 py-3 font-tabular">{formatUsd(token.volume_24h_usd)}</td>
                    <td className="px-4 py-3 font-tabular">{formatUsd(token.liquidity_usd)}</td>
                    <td className="px-4 py-3 font-tabular">{formatUsd(token.fdv_usd)}</td>
                    <td className="px-4 py-3 font-tabular">{formatUsd(token.market_cap_usd)}</td>
                    <td className="px-4 py-3 text-text-faint">—</td>
                  </tr>
                ))}
            </tbody>
          </table>

          {!isLoading && tokens?.length === 0 && (
            <EmptyState
              title="No tokens yet"
              description="Run the ingestion script to populate the screener."
            />
          )}
        </div>
      )}
    </div>
  );
}