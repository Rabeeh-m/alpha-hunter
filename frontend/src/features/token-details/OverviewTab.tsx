import type { Token } from "../../types/tokens";
import { Badge } from "../../components/ui/Badge";

function formatUsd(value: string | null): string {
  if (value === null) return "—";
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 6 })}`;
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

const statVariants = [
  "border-l-brand-primary",
  "border-l-brand-success",
  "border-l-brand-info",
  "border-l-brand-warning",
  "border-l-brand-danger",
  "border-l-brand-primary",
];

export function OverviewTab({ token }: { token: Token }) {
  const stats = [
    { label: "Price", value: formatUsd(token.price_usd) },
    { label: "Liquidity", value: formatUsd(token.liquidity_usd) },
    { label: "24H Volume", value: formatUsd(token.volume_24h_usd) },
    { label: "Market Cap", value: formatUsd(token.market_cap_usd) },
    { label: "FDV", value: formatUsd(token.fdv_usd) },
    { label: "Holders", value: token.holder_count?.toLocaleString() ?? "—" },
  ];

  return (
    <div>
      <div className="mb-5 flex items-center gap-2">
        <Badge variant={chainVariant(token.chain)}>{token.chain}</Badge>
        {token.dex && <Badge variant="info">{token.dex}</Badge>}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((s, i) => (
          <div key={s.label} className={`rounded-xl border border-border bg-bg-surface p-5 shadow-card transition-all hover:shadow-card-hover border-l-4 ${statVariants[i]}`}>
            <p className="text-xs font-medium tracking-wide text-text-muted uppercase">{s.label}</p>
            <p className="mt-2 font-mono text-xl font-bold tabular-nums text-text-primary">{s.value}</p>
          </div>
        ))}
      </div>
      <p className="mt-5 rounded-xl border border-border bg-bg-surface px-4 py-3 font-mono text-xs text-text-muted break-all">
        {token.contract_address}
      </p>
    </div>
  );
}
