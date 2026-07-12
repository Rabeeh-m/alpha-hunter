import { useQuery } from "@tanstack/react-query";
import { fetchTokens } from "../api/tokens";

export function useTokens(limit = 50, offset = 0) {
  return useQuery({
    queryKey: ["tokens", limit, offset],
    queryFn: () => fetchTokens(limit, offset),
    staleTime: 30_000, // matches backend's 60s cache TTL loosely — avoid refetch storms
    refetchInterval: 60_000,
  });
}