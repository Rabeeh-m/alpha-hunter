import { useState } from "react";
import { useParams } from "react-router-dom";

const TABS = [
  "Overview", "Charts", "Liquidity", "Transactions", "Whales",
  "Social", "Developer", "Contract", "Narratives", "Historical", "Risk",
];

export function TokenDetailsPage() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState("Overview");

  return (
    <div>
      <h1 className="mb-4 font-mono text-lg text-text-primary">Token {id}</h1>
      <div className="mb-4 flex gap-1 overflow-x-auto border-b border-border">
        {TABS.map((tab) => (
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
      <div className="py-12 text-center text-text-muted text-sm">
        {activeTab} — implemented in a future milestone.
      </div>
    </div>
  );
}