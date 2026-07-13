export interface TokenSnapshot {
  captured_at: string;
  price_usd: string | null;
  liquidity_usd: string | null;
  volume_24h_usd: string | null;
  market_cap_usd: string | null;
  fdv_usd: string | null;
}