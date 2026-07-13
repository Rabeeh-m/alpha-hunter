import { useQuery } from "@tanstack/react-query";
import { fetchTokens } from "../api/tokens";
import type { TokenQueryParams } from "../types/tokens";

export function useTokens(params: TokenQueryParams = {}) {
  return useQuery({
    queryKey: ["tokens", params],
    queryFn: () => fetchTokens(params),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}