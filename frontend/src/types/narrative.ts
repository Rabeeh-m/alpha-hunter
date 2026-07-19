export type Narrative =
  | "ai" | "defi" | "gaming" | "rwa" | "infrastructure" | "zk"
  | "privacy" | "depin" | "meme" | "layer2" | "bitcoin_ecosystem" | "other";

export interface NarrativeClassification {
  primary_narrative: Narrative;
  confidence: string;
  reasoning: string;
  classified_at: string;
}
