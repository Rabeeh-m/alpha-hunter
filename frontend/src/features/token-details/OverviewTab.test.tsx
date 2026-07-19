import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { OverviewTab } from "./OverviewTab";
import type { Token } from "../../types/tokens";

const mockToken: Token = {
  id: "abc123", chain: "base", contract_address: "0xdeadbeef",
  pair_address: null, name: "Test Coin", symbol: "TEST", dex: "uniswap",
  liquidity_usd: "15000", market_cap_usd: "400000", fdv_usd: "500000",
  volume_24h_usd: "12000", price_usd: "0.0042", holder_count: 314,
  alpha_score: "42", alpha_score_breakdown: null,
  pair_created_at: null,
  created_at: new Date().toISOString(),
};

describe("OverviewTab", () => {
  it("renders formatted stats", () => {
    render(<OverviewTab token={mockToken} />);
    expect(screen.getByText("$15,000")).toBeInTheDocument();
    expect(screen.getByText("314")).toBeInTheDocument();
    expect(screen.getByText("0xdeadbeef")).toBeInTheDocument();
  });
});
