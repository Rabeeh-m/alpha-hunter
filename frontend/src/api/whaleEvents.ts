import { apiClient } from "./client";
import type { WhaleEvent } from "../types/whaleEvent";

export async function fetchRecentWhaleEvents(limit = 50): Promise<WhaleEvent[]> {
  const { data } = await apiClient.get<WhaleEvent[]>("/api/v1/whales/recent", { params: { limit } });
  return data;
}
