import { apiClient } from "./client";
import type { NarrativeClassification } from "../types/narrative";

export async function fetchTokenNarrative(tokenId: string): Promise<NarrativeClassification | null> {
  try {
    const { data } = await apiClient.get<NarrativeClassification>(`/api/v1/tokens/${tokenId}/narrative`);
    return data;
  } catch (err: any) {
    if (err.response?.status === 404) return null;
    throw err;
  }
}

export async function classifyTokenNarrative(tokenId: string): Promise<void> {
  await apiClient.post(`/api/v1/tokens/${tokenId}/narrative/classify`);
}

export async function fetchNarrativeDistribution(): Promise<Record<string, number>> {
  const { data } = await apiClient.get<Record<string, number>>("/api/v1/narratives/distribution");
  return data;
}
