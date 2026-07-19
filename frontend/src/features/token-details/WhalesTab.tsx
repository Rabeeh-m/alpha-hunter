import { useTokenWallets, useScanTokenWallets } from "../../hooks/useTokenWallets";
import { Badge } from "../../components/ui/Badge";
import { Skeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";

function truncate(address: string): string {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

export function WhalesTab({ tokenId }: { tokenId: string }) {
  const { data: holdings, isLoading } = useTokenWallets(tokenId);
  const scan = useScanTokenWallets(tokenId);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs text-text-muted">
          Approximate top holders, reconstructed from recent transfer history — not exact on-chain balances.
        </p>
        <button
          onClick={() => scan.mutate()}
          disabled={scan.isPending}
          className="rounded border border-border px-3 py-1.5 text-xs text-text-primary hover:bg-bg-elevated disabled:opacity-50"
        >
          {scan.isPending ? "Scanning..." : "Scan holders"}
        </button>
      </div>

      {isLoading && <Skeleton className="h-40 w-full" />}

      {!isLoading && (!holdings || holdings.length === 0) && (
        <EmptyState title="No scan data yet" description="Click 'Scan holders' to fetch approximate top holders." />
      )}

      {!isLoading && holdings && holdings.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-text-muted">
              <th className="px-3 py-2 font-medium">Rank</th>
              <th className="px-3 py-2 font-medium">Address</th>
              <th className="px-3 py-2 font-medium">Tag</th>
              <th className="px-3 py-2 font-medium">Approx. Balance</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((h) => (
              <tr key={h.address} className="border-b border-border font-mono text-xs">
                <td className="px-3 py-2 text-text-faint">#{h.rank}</td>
                <td className="px-3 py-2 text-text-primary">{truncate(h.address)}</td>
                <td className="px-3 py-2">
                  {h.wallet_type !== "unknown" ? (
                    <Badge variant="info">{h.wallet_type.replace("_", " ")}</Badge>
                  ) : (
                    <span className="text-text-faint">—</span>
                  )}
                </td>
                <td className="px-3 py-2 font-tabular">{Number(h.approximate_balance).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
