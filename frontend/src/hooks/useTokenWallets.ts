import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchTokenWallets, scanTokenWallets } from "../api/wallets";
import { useToastStore } from "../store/toastStore";

export function useTokenWallets(tokenId: string | undefined) {
  return useQuery({
    queryKey: ["token-wallets", tokenId],
    queryFn: () => fetchTokenWallets(tokenId!),
    enabled: !!tokenId,
  });
}

export function useScanTokenWallets(tokenId: string | undefined) {
  const queryClient = useQueryClient();
  const pushToast = useToastStore((s) => s.push);

  return useMutation({
    mutationFn: () => scanTokenWallets(tokenId!),
    onSuccess: (result) => {
      pushToast({ variant: "success", message: `Scan complete: ${result.holders_found} holders found` });
      queryClient.invalidateQueries({ queryKey: ["token-wallets", tokenId] });
    },
    onError: (error: Error) => {
      pushToast({ variant: "error", message: error.message });
    },
  });
}