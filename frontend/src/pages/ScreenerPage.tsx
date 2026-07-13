import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ChevronDown, ChevronUp, RefreshCw, Search } from "lucide-react";
import { useTokens } from "../hooks/useTokens";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { Badge } from "../components/ui/Badge";
import type { Chain } from "../types/tokens";
import { AlphaScoreBadge } from "../components/ui/AlphaScoreBadge";


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
  { key: "alpha_score", label: "Alpha" },
] as const;

function formatUsd(value: string | null): string {
  if (value === null) return "—";
  const n = Number(value);
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

const chainVariant = (chain: string) => {
  const map: Record<string, "info" | "warning" | "success" | "primary" | "neutral"> = {
    ethereum: "info",
    base: "primary",
    solana: "warning",
    bnb_chain: "warning",
    arbitrum: "info",
    polygon: "primary",
    avalanche: "danger",
    optimism: "success",
  };
  return map[chain] ?? "neutral";
};

export function ScreenerPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [localSearch, setLocalSearch] = useState(searchParams.get("search") ?? "");
  const debouncedSearch = useDebouncedValue(localSearch, 400);

  const chain = (searchParams.get("chain") as Chain) || undefined;
  const sort = searchParams.get("sort") ?? "-created_at";
  const page = Number(searchParams.get("page") ?? "1");

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
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Token Screener</h1>
          <p className="mt-1 text-sm text-text-secondary">Discover and filter tokens across chains</p>
        </div>
        <button onClick={() => refetch()} className="inline-flex items-center gap-2 rounded-xl border border-border bg-bg-surface px-4 py-2.5 text-sm font-medium text-text-secondary shadow-card transition-all hover:bg-bg-hover hover:text-text-primary hover:shadow-card-hover">
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            placeholder="Search symbol or name..."
            className="w-full rounded-xl border border-border bg-bg-surface py-2.5 pl-9 pr-3 text-sm text-text-primary placeholder:text-text-muted shadow-card transition-all focus:outline-none focus:ring-2 focus:ring-brand-primary/30 focus:border-brand-primary"
          />
        </div>
        <select
          value={chain ?? ""}
          onChange={(e) => updateParam("chain", e.target.value || null)}
          className="rounded-xl border border-border bg-bg-surface px-3 py-2.5 text-sm text-text-primary shadow-card transition-all focus:outline-none focus:ring-2 focus:ring-brand-primary/30 focus:border-brand-primary"
        >
          <option value="">All chains</option>
          {CHAINS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {!isError && (
        <>
          <div className="overflow-hidden rounded-xl border border-border bg-bg-surface shadow-card">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-bg text-left text-xs text-text-muted">
                  {SORTABLE_COLUMNS.map((col) => {
                    const isActive = sort.replace("-", "") === col.key;
                    const isDesc = sort === `-${col.key}`;
                    return (
                      <th key={col.key} onClick={() => toggleSort(col.key)} className="cursor-pointer select-none px-5 py-3.5 font-semibold uppercase tracking-wider hover:text-text-primary transition-colors">
                        <span className="inline-flex items-center gap-1.5">
                          {col.label}
                          {isActive && (isDesc ? <ChevronDown size={12} /> : <ChevronUp size={12} />)}
                        </span>
                      </th>
                    );
                  })}
                  <th className="px-5 py-3.5 font-semibold uppercase tracking-wider">Chain</th>
                </tr>
              </thead>
              <tbody>
                {isLoading &&
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-border-light">
                      {Array.from({ length: 8 }).map((_, j) => (
                        <td key={j} className="px-5 py-4"><Skeleton className="h-4 w-20" /></td>
                      ))}
                    </tr>
                  ))}

                {!isLoading &&
                  data?.items.map((token) => (
                    <tr key={token.id} onClick={() => navigate(`/tokens/${token.id}`)} className="cursor-pointer border-b border-border-light transition-colors hover:bg-bg-hover last:border-0">
                      <td className="px-5 py-4 font-medium text-text-primary">{token.symbol}</td>
                      <td className="px-5 py-4 font-mono text-sm tabular-nums text-text-primary">{formatUsd(token.price_usd)}</td>
                      <td className="px-5 py-4 font-mono text-sm tabular-nums text-text-secondary">{formatUsd(token.volume_24h_usd)}</td>
                      <td className="px-5 py-4 font-mono text-sm tabular-nums text-text-secondary">{formatUsd(token.liquidity_usd)}</td>
                      <td className="px-5 py-4 font-mono text-sm tabular-nums text-text-secondary">{formatUsd(token.fdv_usd)}</td>
                      <td className="px-5 py-4 font-mono text-sm tabular-nums text-text-secondary">{formatUsd(token.market_cap_usd)}</td>
                      <td className="px-4 py-3"><AlphaScoreBadge score={token.alpha_score} /></td>
                      <td className="px-5 py-4"><Badge variant={chainVariant(token.chain)}>{token.chain}</Badge></td>
                    </tr>
                  ))}
              </tbody>
            </table>

            {!isLoading && data?.items.length === 0 && (
              <EmptyState title="No tokens match" description="Try a different search or filter." />
            )}
          </div>

          {data && data.total_pages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm">
              <span className="text-text-muted">Page {data.page} of {data.total_pages} — {data.total} tokens</span>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => updateParam("page", String(page - 1), false)}
                  className="rounded-xl border border-border bg-bg-surface px-4 py-2 text-sm font-medium text-text-secondary shadow-card transition-all hover:bg-bg-hover hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Prev
                </button>
                <button
                  disabled={page >= data.total_pages}
                  onClick={() => updateParam("page", String(page + 1), false)}
                  className="rounded-xl border border-border bg-bg-surface px-4 py-2 text-sm font-medium text-text-secondary shadow-card transition-all hover:bg-bg-hover hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-40"
                >
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
