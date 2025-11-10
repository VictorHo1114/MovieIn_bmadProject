// lib/movieAdapter.ts
// 將不同 API 格式的電影資料轉換為 MovieCard 組件所需的格式

import type { RecommendedMovie } from "@/features/recommendation/services";

/**
 * 將任何電影資料格式轉換為 RecommendedMovie 格式
 * 這樣所有頁面都可以使用統一的 MovieCard 組件
 */
export function toMovieCardFormat(movie: any): RecommendedMovie {
  return {
    id: movie.id || movie.movie_id || String(movie.tmdb_id || ''),
    title: movie.title || '',
    overview: movie.overview || '',
    poster_url: movie.poster_url || (movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : null) || '',
    vote_average: movie.vote_average || movie.rating || 0,
    release_year: movie.release_year || 
                  movie.year || 
                  (movie.release_date ? new Date(movie.release_date).getFullYear() : undefined),
  };
}

/**
 * 批量轉換電影陣列
 */
export function toMovieCardList(movies: any[]): RecommendedMovie[] {
  return movies.map(toMovieCardFormat);
}
