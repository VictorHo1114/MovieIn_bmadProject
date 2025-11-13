export interface RecommendedMovie {
  id: string;
  title: string;
  overview: string;
  poster_url: string;
  vote_average: number;
  release_year?: number;
  similarity_score?: number;
  feature_score?: number;
  embedding_score?: number;  // Phase 3.6 新增 ⭐
  match_ratio?: number;       // Phase 3.6 新增 ⭐
  final_score?: number;       // Phase 3.6 新增 ⭐
  quadrant?: string;          // Phase 3.6 新增 ⭐
  genres?: string[];
  release_date?: string;
  runtime?: number;
  actors?: string[];
}

export async function getSimpleRecommendations(
  query: string,
  genres: string[],
  moods: string[],
  eras: string[],
  usePhase36: boolean = true  // Phase 3.6 預設啟用 ⭐
): Promise<{ movies: RecommendedMovie[]; strategy: string; version?: string }> {
  try {
    const response = await fetch("http://localhost:8000/api/recommend/v2/movies", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        selected_genres: genres,
        selected_moods: moods,
        selected_eras: eras,
        randomness: 0.3,
        decision_threshold: 40,
        use_legacy: false,
        use_phase36: usePhase36,  // Phase 3.6 開關 ⭐
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    
    return {
      movies: data.movies || [],
      strategy: data.strategy || "",
      version: data.version,  // "3.5" or "3.6"
    };
  } catch (error) {
    console.error("Error fetching recommendations:", error);
    throw error;
  }
}
