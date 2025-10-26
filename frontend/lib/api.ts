import { getJSON } from "./http";
import type { HomeFeed, Profile, SearchResult } from "./types";

export const Api = {
  home: () => getJSON<HomeFeed>("/home"),
  profile: {
    me: () => getJSON<Profile>("/profile/me"),
  },
  search: (q: string) =>
    getJSON<SearchResult>(`/search?q=${encodeURIComponent(q)}`),
};
