export interface SocialFactor {
  score: number;
  weight: number;
}

export interface SocialScore {
  score: number;
  factor_breakdown: {
    member_size: SocialFactor;
    activity: SocialFactor;
    member_growth: SocialFactor;
    possible_inorganic_growth: boolean;
    composite: number;
  };
  possible_inorganic_growth: boolean;
  scanned_at: string;
}
