export interface WalletHolding {
  address: string;
  wallet_type: "unknown" | "whale" | "smart_money" | "vc" | "exchange" | "influencer" | "early_adopter";
  confidence_score: string | null;
  approximate_balance: string;
  rank: number;
  scanned_at: string;
}
