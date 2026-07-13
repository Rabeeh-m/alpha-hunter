import { useState } from "react";
import { useParams } from "react-router-dom";
import { useToken } from "../hooks/useTokenDetail";
import { OverviewTab } from "../features/token-details/OverviewTab";
import { ChartsTab } from "../features/token-details/ChartsTab";
import { Skeleton } from "../components/ui/Skeleton";
import { ErrorState } from "../components/ui/ErrorState";

const LIVE_TABS = ["Overview", "Charts"] as const;
const PLACEHOLDER_TABS = [
  "Liquidity", "Transactions", "Whales", "Social",
  "Developer", "Contract", "Narratives", "Risk",
];
const ALL_TABS = [...LIVE_TABS, ...PLACEHOLDER_TABS];

export function TokenDetailsPage() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState<string>("Overview");
  const { data: token, isLoading, isError, error, refetch } = useToken(id);

  return (
    <div>
      {isLoading && <Skeleton className="h-8 w-48 mb-4" />}
      {!isLoading && token && (
        <h1 className="mb-4 font-mono text-lg text-text-primary">{token.symbol}</h1>
      )}

      <div className="mb-4 flex gap-1 overflow-x-auto border-b border-border">
        {ALL_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-2 text-sm whitespace-nowrap ${
              activeTab === tab
                ? "border-b-2 border-accent-gain text-text-primary"
                : "text-text-muted hover:text-text-primary"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {isLoading && <Skeleton className="h-40 w-full" />}
      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {!isLoading && !isError && token && (
        <>
          {activeTab === "Overview" && <OverviewTab token={token} />}
          {activeTab === "Charts" && <ChartsTab tokenId={token.id} />}
          {!LIVE_TABS.includes(activeTab as (typeof LIVE_TABS)[number]) && (
            <div className="py-12 text-center text-sm text-text-muted">
              {activeTab} — implemented in a future milestone.
            </div>
          )}
        </>
      )}
    </div>
  );
}