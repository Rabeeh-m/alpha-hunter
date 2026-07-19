import { apiClient } from "./client";
import type { WalletHolding } from "../types/wallet";

export async function fetchTokenWallets(tokenId: string): Promise<WalletHolding[]> {
  const { data } = await apiClient.get<WalletHolding[]>(`/api/v1/tokens/${tokenId}/wallets`);
  return data;
}

export async function scanTokenWallets(tokenId: string): Promise<{ status: string; holders_found: number }> {
  const { data } = await apiClient.post(`/api/v1/tokens/${tokenId}/wallets/scan`);
  return data;
}
