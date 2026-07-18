import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchDeveloperActivity, scanDeveloperActivity } from "../api/developerActivity";
import { useToastStore } from "../store/toastStore";

export function useDeveloperActivity(tokenId: string | undefined) {
  return useQuery({
    queryKey: ["developer-activity", tokenId],
    queryFn: () => fetchDeveloperActivity(tokenId!),
    enabled: !!tokenId,
  });
}

export function useScanDeveloperActivity(tokenId: string | undefined) {
  const queryClient = useQueryClient();
  const pushToast = useToastStore((s) => s.push);

  return useMutation({
    mutationFn: () => scanDeveloperActivity(tokenId!),
    onSuccess: (result) => {
      pushToast({ variant: "success", message: `Scan complete: score ${result.score}` });
      queryClient.invalidateQueries({ queryKey: ["developer-activity", tokenId] });
    },
    onError: (error: Error) => pushToast({ variant: "error", message: error.message }),
  });
}
