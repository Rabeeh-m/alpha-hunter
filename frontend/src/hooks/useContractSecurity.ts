import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchContractSecurity, scanContractSecurity } from "../api/contractSecurity";
import { useToastStore } from "../store/toastStore";

export function useContractSecurity(tokenId: string | undefined) {
  return useQuery({
    queryKey: ["contract-security", tokenId],
    queryFn: () => fetchContractSecurity(tokenId!),
    enabled: !!tokenId,
  });
}

export function useScanContractSecurity(tokenId: string | undefined) {
  const queryClient = useQueryClient();
  const pushToast = useToastStore((s) => s.push);

  return useMutation({
    mutationFn: () => scanContractSecurity(tokenId!),
    onSuccess: (result) => {
      pushToast({ variant: result.safety_score >= 70 ? "success" : "info", message: `Scan complete: safety score ${result.safety_score}` });
      queryClient.invalidateQueries({ queryKey: ["contract-security", tokenId] });
    },
    onError: (error: Error) => pushToast({ variant: "error", message: error.message }),
  });
}
