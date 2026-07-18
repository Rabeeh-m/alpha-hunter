import { apiClient } from "./client";
import type { DeveloperActivity } from "../types/developerActivity";

export async function fetchDeveloperActivity(tokenId: string): Promise<DeveloperActivity | null> {
  try {
    const { data } = await apiClient.get<DeveloperActivity>(`/api/v1/tokens/${tokenId}/developer`);
    return data;
  } catch (err: any) {
    if (err.response?.status === 404) return null;
    throw err;
  }
}

export async function scanDeveloperActivity(tokenId: string): Promise<{ status: string; score: number }> {
  const { data } = await apiClient.post(`/api/v1/tokens/${tokenId}/developer/scan`);
  return data;
}
