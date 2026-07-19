import { useSocialScore, useScanSocialScore } from "../../hooks/useSocialScore";
import { Skeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";
import { Badge } from "../../components/ui/Badge";

export function SocialTab({ tokenId }: { tokenId: string }) {
  const { data: social, isLoading } = useSocialScore(tokenId);
  const scan = useScanSocialScore(tokenId);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs text-text-muted">
          Telegram community signal only — Twitter/X excluded (API access requires a paid tier).
        </p>
        <button
          onClick={() => scan.mutate()}
          disabled={scan.isPending}
          className="rounded border border-border px-3 py-1.5 text-xs text-text-primary hover:bg-bg-elevated disabled:opacity-50"
        >
          {scan.isPending ? "Scanning..." : social ? "Re-scan" : "Scan Telegram"}
        </button>
      </div>

      {isLoading && <Skeleton className="h-40 w-full" />}

      {!isLoading && !social && (
        <EmptyState title="No social scan yet" description="Only works if this token has a linked Telegram channel." />
      )}

      {!isLoading && social && (
        <div>
          <div className="mb-4 flex items-center gap-3 rounded border border-border bg-bg-surface p-4">
            <div>
              <p className="text-xs text-text-muted">Social Score</p>
              <p className="mt-1 font-mono text-3xl text-accent-gain">{social.score}<span className="text-sm text-text-faint">/100</span></p>
            </div>
            {social.possible_inorganic_growth && (
              <Badge variant="signal">Possible inorganic growth detected</Badge>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
