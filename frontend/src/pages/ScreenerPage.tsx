import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useTokens } from "../hooks/useTokens";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { Badge } from "../components/ui/Badge";
import type { Chain } from "../types/tokens";

const CHAINS: Chain[] = [
  "ethereum", "base", "solana", "bnb_chain", "arbitrum", "polygon", "avalanche", "optimism",
];

const SORTABLE_COLUMNS = [
  { key: "symbol", label: "Token" },
  { key: "price_usd", label: "Price" },
  { key: "volume_24h_usd", label: "24H Vol" },
  { key: "liquidity_usd", label: "Liquidity" },
  { key: "fdv_usd", label: "FDV" },
  { key: "market_cap_usd", label: "Mkt Cap" },
] as const;

function formatUsd(value: string | null): string {
  if (value === null) return "—";
  const n = Number(value);
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

export function ScreenerPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [localSearch, setLocalSearch] = useState(searchParams.get("search") ?? "");
  const debouncedSearch = useDebouncedValue(localSearch, 400);

  const chain = (searchParams.get("chain") as Chain) || undefined;
  const sort = searchParams.get("sort") ?? "-created_at";
  const page = Number(searchParams.get("page") ?? "1");

  // URL is the single source of truth for filters -- shareable, survives refresh.
  useEffect(() => {
    const next = new URLSearchParams(searchParams);
    if (debouncedSearch) next.set("search", debouncedSearch);
    else next.delete("search");
    next.set("page", "1");
    setSearchParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  function updateParam(key: string, value: string | null, resetPage = true) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    if (resetPage) next.set("page", "1");
    setSearchParams(next);
  }

  function toggleSort(key: string) {
    updateParam("sort", sort === `-${key}` ? key : `-${key}`, false);
  }

  const { data, isLoading, isError, error, refetch } = useTokens({
    search: searchParams.get("search") || undefined,
    chain, sort, page, page_size: 25,
  });

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-text-primary">Token Screener</h1>
        <button onClick={() => refetch()} className="rounded border border-border px-3 py-1.5 text-sm text-text-muted hover:bg-bg-elevated hover:text-text-primary">
          Refresh
        </button>
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <input
          value={localSearch}
          onChange={(e) => setLocalSearch(e.target.value)}
          placeholder="Search symbol or name..."
          className="rounded border border-border bg-bg-elevated px-3 py-1.5 text-sm text-text-primary placeholder:text-text-faint focus:outline-none focus:ring-1 focus:ring-accent-gain"
        />
        <select
          value={chain ?? ""}
          onChange={(e) => updateParam("chain", e.target.value || null)}
          className="rounded border border-border bg-bg-elevated px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-gain"
        >
          <option value="">All chains</option>
          {CHAINS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {!isError && (
        <>
          <div className="overflow-x-auto rounded border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-bg-surface text-left text-xs text-text-muted">
                  {SORTABLE_COLUMNS.map((col) => {
                    const isActive = sort.replace("-", "") === col.key;
                    const isDesc = sort === `-${col.key}`;
                    return (
                      <th key={col.key} onClick={() => toggleSort(col.key)} className="cursor-pointer select-none px-4 py-2 font-medium hover:text-text-primary">
                        <span className="inline-flex items-center gap-1">
                          {col.label}
                          {isActive && (isDesc ? <ChevronDown size={12} /> : <ChevronUp size={12} />)}
                        </span>
                      </th>
                    );
                  })}
                  <th className="px-4 py-2 font-medium">Chain</th>
                </tr>
              </thead>
              <tbody>
                {isLoading &&
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-border">
                      {Array.from({ length: 7 }).map((_, j) => (
                        <td key={j} className="px-4 py-3"><Skeleton className="h-4 w-16" /></td>
                      ))}
                    </tr>
                  ))}

                {!isLoading &&
                  data?.items.map((token) => (
                    <tr key={token.id} onClick={() => navigate(`/tokens/${token.id}`)} className="cursor-pointer border-b border-border font-mono text-xs hover:bg-bg-surface">
                      <td className="px-4 py-3 font-sans font-medium text-text-primary">{token.symbol}</td>
                      <td className="px-4 py-3 font-tabular">{formatUsd(token.price_usd)}</td>
                      <td className="px-4 py-3 font-tabular">{formatUsd(token.volume_24h_usd)}</td>
                      <td className="px-4 py-3 font-tabular">{formatUsd(token.liquidity_usd)}</td>
                      <td className="px-4 py-3 font-tabular">{formatUsd(token.fdv_usd)}</td>
                      <td className="px-4 py-3 font-tabular">{formatUsd(token.market_cap_usd)}</td>
                      <td className="px-4 py-3"><Badge variant="neutral">{token.chain}</Badge></td>
                    </tr>
                  ))}
              </tbody>
            </table>

            {!isLoading && data?.items.length === 0 && (
              <EmptyState title="No tokens match" description="Try a different search or filter." />
            )}
          </div>

          {data && data.total_pages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm text-text-muted">
              <span>Page {data.page} of {data.total_pages} — {data.total} tokens</span>
              <div className="flex gap-2">
                <button disabled={page <= 1} onClick={() => updateParam("page", String(page - 1), false)} className="rounded border border-border px-3 py-1 disabled:opacity-30">
                  Prev
                </button>
                <button disabled={page >= data.total_pages} onClick={() => updateParam("page", String(page + 1), false)} className="rounded border border-border px-3 py-1 disabled:opacity-30">
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}