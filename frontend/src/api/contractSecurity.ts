import { apiClient } from "./client";
import type { ContractSecurity } from "../types/contractSecurity";

export async function fetchContractSecurity(tokenId: string): Promise<ContractSecurity | null> {
  try {
    const { data } = await apiClient.get<ContractSecurity>(`/api/v1/tokens/${tokenId}/security`);
    return data;
  } catch (err: any) {
    if (err.response?.status === 404) return null;
    throw err;
  }
}

export async function scanContractSecurity(tokenId: string): Promise<{ safety_score: number }> {
  const { data } = await apiClient.post(`/api/v1/tokens/${tokenId}/security/scan`);
  return data;
}