import type { Token } from "../../types/tokens";
import { Badge } from "../../components/ui/Badge";

function formatUsd(value: string | null): string {
  if (value === null) return "—";
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 6 })}`;
}

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
      <div className="mb-4 flex items-center gap-2">
        <Badge variant="neutral">{token.chain}</Badge>
        {token.dex && <Badge variant="signal">{token.dex}</Badge>}
      </div>
      <div className="grid grid-cols-3 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="rounded border border-border bg-bg-surface p-4">
            <p className="text-xs text-text-muted">{s.label}</p>
            <p className="mt-1 font-mono text-lg text-text-primary">{s.value}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 font-mono text-xs text-text-faint break-all">
        {token.contract_address}
      </p>
    </div>
  );
}