export type WhaleEventType = "new_position" | "increased" | "decreased";

export interface WhaleEvent {
  id: string;
  token_symbol: string;
  token_chain: string;
  wallet_address: string;
  wallet_label: string | null;
  wallet_type: string;
  event_type: WhaleEventType;
  previous_balance: string | null;
  new_balance: string;
  change_pct: string | null;
  change_usd: string | null;
  detected_at: string;
}