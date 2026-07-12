import { apiClient } from "./client";
import type { Token } from "../types/tokens";

export async function fetchTokens(limit = 50, offset = 0): Promise<Token[]> {
  const { data } = await apiClient.get<Token[]>("/api/v1/tokens", {
    params: { limit, offset },
  });
  return data;
}