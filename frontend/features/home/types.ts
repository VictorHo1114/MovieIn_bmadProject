import type { MovieCard } from "@/lib/types";

export interface HomeFeedViewModel {
  trending: MovieCard[];
  lastUpdated: string;
}