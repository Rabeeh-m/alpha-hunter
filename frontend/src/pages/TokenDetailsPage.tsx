import { useState } from "react";
import { useParams } from "react-router-dom";
import { useToken } from "../hooks/useTokenDetail";
import { OverviewTab } from "../features/token-details/OverviewTab";
import { ChartsTab } from "../features/token-details/ChartsTab";
import { Skeleton } from "../components/ui/Skeleton";
import { ErrorState } from "../components/ui/ErrorState";
import clsx from "clsx";
import { WhalesTab } from "../features/token-details/WhalesTab";
import { ContractTab } from "../features/token-details/ContractTab";
import { NarrativesTab } from "../features/token-details/NarrativesTab";
import { DeveloperTab } from "../features/token-details/DeveloperTab";


const LIVE_TABS = ["Overview", "Charts", "Whales", "Contract"] as const;
const PLACEHOLDER_TABS = ["Liquidity", "Transactions", "Social", "Developer", "Narratives", "Risk"];
const ALL_TABS = [...LIVE_TABS, ...PLACEHOLDER_TABS];

export function TokenDetailsPage() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState<string>("Overview");
  const { data: token, isLoading, isError, error, refetch } = useToken(id);

  return (
    <div>
      <div className="mb-6">
        {isLoading && <Skeleton className="h-8 w-48 mb-2" />}
        {!isLoading && token && (
          <h1 className="text-2xl font-semibold tracking-tight text-text-primary">{token.symbol}</h1>
        )}
      </div>

      <div className="mb-6 flex gap-1 overflow-x-auto border-b border-border">
        {ALL_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={clsx(
              "relative px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors",
              activeTab === tab
                ? "text-brand-primary"
                : "text-text-muted hover:text-text-secondary"
            )}
          >
            {tab}
            {activeTab === tab && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-primary rounded-full" />
            )}
          </button>
        ))}
      </div>

      {isLoading && <Skeleton className="h-48 w-full rounded-xl" />}
      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {!isLoading && !isError && token && (
        <>
          {activeTab === "Overview" && <OverviewTab token={token} />}
          {activeTab === "Charts" && <ChartsTab tokenId={token.id} />}
          {activeTab === "Whales" && <WhalesTab tokenId={token.id} />}
          {activeTab === "Contract" && <ContractTab tokenId={token.id} />}
          {activeTab === "narrative" && <NarrativesTab tokenId={token.id} />}
          {activeTab === "developer" && <DeveloperTab tokenId={token.id} />}

          {!LIVE_TABS.includes(activeTab as (typeof LIVE_TABS)[number]) && (
            <div className="py-16 text-center text-sm text-text-muted">
              {activeTab} — implemented in a future milestone.
            </div>
          )}
        </>
      )}
    </div>
  );
}
