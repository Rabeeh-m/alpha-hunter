import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { classifyTokenNarrative, fetchNarrativeDistribution, fetchTokenNarrative } from "../api/narratives";
import { useToastStore } from "../store/toastStore";

export function useTokenNarrative(tokenId: string | undefined) {
  return useQuery({
    queryKey: ["narrative", tokenId],
    queryFn: () => fetchTokenNarrative(tokenId!),
    enabled: !!tokenId,
  });
}

export function useClassifyNarrative(tokenId: string | undefined) {
  const queryClient = useQueryClient();
  const pushToast = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: () => classifyTokenNarrative(tokenId!),
    onSuccess: () => {
      pushToast({ variant: "success", message: "Classification complete" });
      queryClient.invalidateQueries({ queryKey: ["narrative", tokenId] });
    },
    onError: (error: Error) => pushToast({ variant: "error", message: error.message }),
  });
}

export function useNarrativeDistribution() {
  return useQuery({ queryKey: ["narrative-distribution"], queryFn: fetchNarrativeDistribution, refetchInterval: 60_000 });
}