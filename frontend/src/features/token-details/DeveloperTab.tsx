import { useDeveloperActivity, useScanDeveloperActivity } from "../../hooks/useDeveloperActivity";
import { Skeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";
import { Badge } from "../../components/ui/Badge";

export function DeveloperTab({ tokenId }: { tokenId: string }) {
  const { data, isLoading } = useDeveloperActivity(tokenId);
  const scan = useScanDeveloperActivity(tokenId);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs text-text-muted">Only works if a GitHub repository is linked — most tokens have none.</p>
        <button onClick={() => scan.mutate()} disabled={scan.isPending} className="rounded border border-border px-3 py-1.5 text-xs text-text-primary hover:bg-bg-elevated disabled:opacity-50">
          {scan.isPending ? "Scanning..." : "Scan repository"}
        </button>
      </div>

      {isLoading && <Skeleton className="h-40 w-full" />}
      {!isLoading && !data && <EmptyState title="No scan data yet" description="Click 'Scan repository' — requires a linked GitHub link." />}

      {!isLoading && data && (
        <div>
          <div className="mb-4 flex items-center gap-3">
            <p className="font-mono text-3xl text-accent-gain">{data.score}<span className="text-sm text-text-faint">/100</span></p>
            {data.is_fork && <Badge variant="signal">Fork</Badge>}
            {data.is_archived && <Badge variant="loss">Archived</Badge>}
          </div>
          <div className="mb-4 grid grid-cols-4 gap-3 text-xs">
            <div><p className="text-text-muted">Stars</p><p className="font-mono text-text-primary">{data.stars}</p></div>
            <div><p className="text-text-muted">Forks</p><p className="font-mono text-text-primary">{data.forks}</p></div>
            <div><p className="text-text-muted">Contributors</p><p className="font-mono text-text-primary">{data.contributors_count}+</p></div>
            <div><p className="text-text-muted">Last Commit</p><p className="font-mono text-text-primary">{data.last_commit_at ? new Date(data.last_commit_at).toLocaleDateString() : "—"}</p></div>
          </div>
          <ul className="space-y-1">
            {data.flags.map((f: string, i: number) => (
              <li key={i} className="rounded border border-border bg-bg-surface px-3 py-2 text-xs text-text-primary">{f}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}