import { getJSON } from "./http";
import type { HomeFeed, Profile, SearchResult } from "./types";

export const Api = {
  home: () => getJSON<HomeFeed>("/home"),
  profile: {
    me: () => getJSON<Profile>("/profile/me"),
  },
  search: (q: string) =>
    getJSON<SearchResult>(`/search?q=${encodeURIComponent(q)}`),
  getRecommendations: (params: {
    query: string;
    genres: string[];
    moods: string[];
    eras: string[];
  }) => getJSON<{ movies: any[]; strategy: string }>("/recommendations", {
    method: "POST",
    body: JSON.stringify(params),
  }),
};
