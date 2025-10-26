import { Api } from "@/lib/api";
import { USE_MOCKS } from "@/lib/config";
import type { HomeFeedViewModel } from "./types";

export async function getHomeFeed(): Promise<HomeFeedViewModel> {
  if (USE_MOCKS) {
    return {
      trending: [
        { id: "1", title: "Inception", year: 2010, rating: 8.8 },
        { id: "2", title: "Interstellar", year: 2014, rating: 8.6 },
        { id: "3", title: "La La Land", year: 2016, rating: 8.0 },
        { id: "4", title: "Whiplash", year: 2014, rating: 8.5 },
        { id: "5", title: "Dune: Part Two", year: 2024, rating: 8.7 },
      ],
      lastUpdated: new Date().toISOString(),
    };
  }

  const data = await Api.home();
  return {
    trending: data.trending.map((m) => ({ ...m, rating: Number(m.rating) })),
    lastUpdated: new Date().toISOString(),
  };
}
