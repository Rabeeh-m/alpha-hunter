import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect } from "vitest";
import { JobCard } from "./JobCard";
import type { Job } from "../../types/job";

const mockJob: Job = {
  id: "refresh_dexscreener",
  name: "DexScreener Refresh",
  description: "Fetch latest tokens",
  category: "collector",
  enabled: true,
  interval_seconds: 90,
  execution_count: 10,
  success_count: 9,
  failure_count: 1,
  last_run_at: new Date().toISOString(),
  last_duration_ms: 340,
  last_status: "success",
  next_run_at: null,
};

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient();
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("JobCard", () => {
  it("renders job name and success rate", () => {
    renderWithQueryClient(<JobCard job={mockJob} />);
    expect(screen.getByText("DexScreener Refresh")).toBeInTheDocument();
    expect(screen.getByText("90%")).toBeInTheDocument();
  });
});
