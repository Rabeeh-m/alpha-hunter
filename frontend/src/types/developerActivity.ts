export interface DeveloperActivity {
  score: number;
  flags: string[];
  stars: number;
  forks: number;
  contributors_count: number;
  last_commit_at: string | null;
  is_fork: boolean;
  is_archived: boolean;
  scanned_at: string;
}
