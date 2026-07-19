import { useQuery } from "@tanstack/react-query";
import { fetchRecentWhaleEvents } from "../api/whaleEvents";

export function useRecentWhaleEvents(limit = 50) {
  return useQuery({
    queryKey: ["whale-events", limit],
    queryFn: () => fetchRecentWhaleEvents(limit),
    refetchInterval: 30_000,
  });
}
