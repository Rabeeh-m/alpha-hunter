export interface SocialFactorBreakdown {
  member_size: { score: number; weight: number };
  activity: { score: number; weight: number };
  member_growth: { score: number; weight: number };
  possible_inorganic_growth: boolean;
  composite: number;
}
export interface SocialScore {
  score: number;
  factor_breakdown: SocialFactorBreakdown;
  possible_inorganic_growth: boolean;
  scanned_at: string;
}