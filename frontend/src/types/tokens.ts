export type Chain =
  | "ethereum" | "base" | "solana" | "bnb_chain"
  | "arbitrum" | "polygon" | "avalanche" | "optimism";

export interface Token {
  alpha_score_breakdown: any;
  alpha_score: string;
  id: string;
  chain: Chain;
  contract_address: string;
  pair_address: string | null;
  name: string;
  symbol: string;
  dex: string | null;
  liquidity_usd: string | null;
  market_cap_usd: string | null;
  fdv_usd: string | null;
  volume_24h_usd: string | null;
  price_usd: string | null;
  holder_count: number | null;
  created_at: string;
}

export interface TokenQueryParams {
  search?: string;
  chain?: Chain;
  min_liquidity?: number;
  min_volume?: number;
  sort?: string;
  page?: number;
  page_size?: number;
}

export interface TokenPage {
  items: Token[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface AlphaFactorBreakdown {
  liquidity: { score: number; weight: number };
  volume: { score: number; weight: number };
  market_cap: { score: number; weight: number };
  age: { score: number; weight: number };
  liquidity_growth: { score: number; weight: number };
  composite: number;
}

