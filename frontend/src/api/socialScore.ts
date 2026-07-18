import { apiClient } from "./client";
import type { SocialScore } from "../types/socialScore";

export async function fetchSocialScore(tokenId: string): Promise<SocialScore | null> {
  try {
    const { data } = await apiClient.get<SocialScore>(`/api/v1/tokens/${tokenId}/social`);
    return data;
  } catch (err: any) {
    if (err.response?.status === 404) return null;
    throw err;
  }
}

export async function scanSocialScore(tokenId: string): Promise<{ status: string; score: number }> {
  const { data } = await apiClient.post(`/api/v1/tokens/${tokenId}/social/scan`);
  return data;
}
