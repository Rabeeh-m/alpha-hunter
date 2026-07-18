import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchSocialScore, scanSocialScore } from "../api/socialScore";
import { useToastStore } from "../store/toastStore";

export function useSocialScore(tokenId: string | undefined) {
  return useQuery({
    queryKey: ["social-score", tokenId],
    queryFn: () => fetchSocialScore(tokenId!),
    enabled: !!tokenId,
  });
}

export function useScanSocialScore(tokenId: string | undefined) {
  const queryClient = useQueryClient();
  const pushToast = useToastStore((s) => s.push);

  return useMutation({
    mutationFn: () => scanSocialScore(tokenId!),
    onSuccess: (result) => {
      pushToast({ variant: "success", message: `Scan complete: score ${result.score}` });
      queryClient.invalidateQueries({ queryKey: ["social-score", tokenId] });
    },
    onError: (error: Error) => pushToast({ variant: "error", message: error.message }),
  });
}
