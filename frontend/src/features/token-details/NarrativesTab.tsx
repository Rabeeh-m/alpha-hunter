import { useClassifyNarrative, useTokenNarrative } from "../../hooks/useNarratives";
import { Skeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";
import { Badge } from "../../components/ui/Badge";

export function NarrativesTab({ tokenId }: { tokenId: string }) {
  const { data: narrative, isLoading } = useTokenNarrative(tokenId);
  const classify = useClassifyNarrative(tokenId);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs text-text-muted">
          Classified from token name/symbol only — a weak signal; low confidence is expected and normal.
        </p>
        <button
          onClick={() => classify.mutate()}
          disabled={classify.isPending}
          className="rounded border border-border px-3 py-1.5 text-xs text-text-primary hover:bg-bg-elevated disabled:opacity-50"
        >
          {classify.isPending ? "Classifying..." : narrative ? "Re-classify" : "Classify"}
        </button>
      </div>

      {isLoading && <Skeleton className="h-24 w-full" />}
      {!isLoading && !narrative && <EmptyState title="Not classified yet" description="Click 'Classify' to run categorization." />}

      {!isLoading && narrative && (
        <div className="rounded border border-border bg-bg-surface p-4">
          <div className="mb-2 flex items-center gap-2">
            <Badge variant="signal">{narrative.primary_narrative.replace("_", " ")}</Badge>
            <span className="font-mono text-xs text-text-muted">{Number(narrative.confidence)}% confidence</span>
          </div>
          <p className="text-sm text-text-primary">{narrative.reasoning}</p>
        </div>
      )}
    </div>
  );
}
