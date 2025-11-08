// app/search/page.tsx

"use client";
import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { API_BASE } from "@/lib/config";
import SearchForm from "@/features/search/SearchForm";

interface Movie {
  id: string;
  title: string;
  overview: string | null;
  poster_url: string | null;
  backdrop_url: string | null;
  release_date: string;
  rating: number;
  vote_count: number;
}

interface PopularMoviesResponse {
  items: Movie[];
  total: number;
}

export default function Page() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const [popular, setPopular] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!query) {
      setLoading(true);
      setError(null);
      fetch(`${API_BASE}/popular/`)
        .then((res) => {
          if (!res.ok) throw new Error(`載入失敗：Status ${res.status}`);
          return res.json();
        })
        .then((data: PopularMoviesResponse) => {
          setPopular(data.items);
        })
        .catch((e) => {
          setError(e?.message ?? "載入失敗");
          setPopular([]);
        })
        .finally(() => setLoading(false));
    }
  }, [query]);

  return (
    <div className="min-h-screen bg-gray-900 px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-white text-center">電影搜尋</h1>
      <SearchForm />
      {!query ? (
        <>
          <h2 className="text-xl font-semibold mb-4 text-white text-center">熱門電影</h2>
          {loading ? (
            <div className="text-white">載入中...</div>
          ) : error ? (
            <div className="text-red-400">錯誤：{error}</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
              {popular.map((movie) => (
                <Link 
                  key={movie.id}
                  href={`/movie/${movie.id}`}
                  className="group"
                >
                  <article className="bg-gray-800 rounded-2xl overflow-hidden shadow-xl hover:shadow-yellow-400/40 transition-all duration-300 hover:-translate-y-1 border border-gray-700">
                    <div className="relative aspect-[2/3]">
                      {movie.poster_url ? (
                        <img
                          src={movie.poster_url}
                          alt={movie.title}
                          className="w-full h-full object-cover group-hover:opacity-80 transition-opacity"
                          loading="lazy"
                        />
                      ) : (
                        <div className="w-full h-full bg-gray-700 flex items-center justify-center text-base text-gray-300">
                          無海報
                        </div>
                      )}
                      <div className="absolute top-2 right-2 px-2 py-1 bg-yellow-400 text-gray-900 text-sm font-bold rounded shadow">
                        ⭐ {movie.rating.toFixed(1)}
                      </div>
                    </div>
                    <div className="p-4">
                      <h2 className="font-bold text-lg mb-2 text-white group-hover:text-yellow-300 transition-colors line-clamp-1">
                        {movie.title}
                      </h2>
                      <div className="text-sm text-gray-300 mb-2">
                        {new Date(movie.release_date).getFullYear()}
                      </div>
                      {movie.overview && (
                        <p className="text-sm text-gray-200 line-clamp-3">
                          {movie.overview}
                        </p>
                      )}
                    </div>
                  </article>
                </Link>
              ))}
            </div>
          )}
        </>
      ) : null}
      {/* 搜尋結果由 SearchForm 自行渲染 */}
    </div>
  );
}