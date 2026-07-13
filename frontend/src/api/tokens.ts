import { apiClient } from "./client";
import type { Token, TokenPage, TokenQueryParams } from "../types/tokens";
import type { TokenSnapshot } from "../types/tokenSnapshot";


export async function fetchTokens(params: TokenQueryParams = {}): Promise<TokenPage> {
  const { data } = await apiClient.get<TokenPage>("/api/v1/tokens", { params });
  return data;
}

export async function fetchTokenById(id: string): Promise<Token> {
  const { data } = await apiClient.get<Token>(`/api/v1/tokens/${id}`);
  return data;
}

export async function fetchTokenSnapshots(id: string, hours = 24): Promise<TokenSnapshot[]> {
  const { data } = await apiClient.get<TokenSnapshot[]>(`/api/v1/tokens/${id}/snapshots`, {
    params: { hours },
  });
  return data;
}