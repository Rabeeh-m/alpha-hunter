export type Chain =
  | "ethereum" | "base" | "solana" | "bnb_chain"
  | "arbitrum" | "polygon" | "avalanche" | "optimism";

export interface Token {
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