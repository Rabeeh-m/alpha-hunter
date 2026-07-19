export interface ContractSecurity {
  safety_score: number;
  flags: string[];
  is_honeypot: boolean;
  is_mintable: boolean;
  is_open_source: boolean;
  buy_tax: string | null;
  sell_tax: string | null;
  owner_address: string | null;
  scanned_at: string;
}
