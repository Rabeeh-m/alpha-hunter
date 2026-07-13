import { useQuery } from "@tanstack/react-query";
import { fetchTokenById, fetchTokenSnapshots } from "../api/tokens";

export function useToken(id: string | undefined) {
  return useQuery({
    queryKey: ["token", id],
    queryFn: () => fetchTokenById(id!),
    enabled: !!id,
    refetchInterval: 60_000,
  });
}

export function useTokenSnapshots(id: string | undefined, hours = 24) {
  return useQuery({
    queryKey: ["token-snapshots", id, hours],
    queryFn: () => fetchTokenSnapshots(id!, hours),
    enabled: !!id,
    refetchInterval: 60_000,
  });
}