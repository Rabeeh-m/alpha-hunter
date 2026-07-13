import { apiClient } from "./client";
import type { TokenPage, TokenQueryParams } from "../types/tokens";

export async function fetchTokens(params: TokenQueryParams = {}): Promise<TokenPage> {
  const { data } = await apiClient.get<TokenPage>("/api/v1/tokens", { params });
  return data;
}