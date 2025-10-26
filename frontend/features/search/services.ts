import { Api } from "@/lib/api";
import { USE_MOCKS } from "@/lib/config";
import type { SearchResult } from "@/lib/types";

export async function searchMovies(q: string): Promise<SearchResult> {
  if (USE_MOCKS) {
    const pool = ["Interstellar", "Inside Out 2", "Oppenheimer", "Barbie", "Dune", "Heat"];
    const items = pool
      .filter((t) => t.toLowerCase().includes(q.toLowerCase()))
      .map((t, i) => ({ id: String(i), title: t, year: 2000 + i, rating: 7.5 + i / 10 }));
    return { items };
  }
  return Api.search(q);
}
