'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { API_BASE } from '@/lib/config'

interface Movie {
  id: string
  title: string
  overview: string | null
  poster_url: string | null
  backdrop_url: string | null
  release_date: string
  rating: number
  vote_count: number
}

interface PopularMoviesResponse {
  items: Movie[]
  total: number
}

export default function PopularMovies() {
  const [movies, setMovies] = useState<Movie[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchPopularMovies() {
      try {
        console.log('Fetching popular movies from:', `${API_BASE}/popular/`)
        const res = await fetch(`${API_BASE}/popular/`)
        if (!res.ok) {
          console.error('Failed to fetch:', res.status, res.statusText)
          throw new Error(`載入失敗：Status ${res.status}`)
        }
        const data = await res.json() as PopularMoviesResponse
        setMovies(data.items)
      } catch (e: any) {
        setError(e?.message ?? '載入失敗')
      } finally {
        setLoading(false)
      }
    }
    fetchPopularMovies()
  }, [])

  if (loading) return <div className="p-6">載入中...</div>
  if (error) return <div className="p-6 text-red-500">錯誤：{error}</div>
  if (!movies.length) return <div className="p-6">目前沒有熱門電影</div>

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">熱門電影</h1>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {movies.map((movie) => (
          <Link 
            key={movie.id}
            href={`/movie/${movie.id}`}
            className="group"
          >
            <article className="bg-gray-800 rounded-lg overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
              <div className="relative aspect-[2/3]">
                {movie.poster_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={movie.poster_url}
                    alt={movie.title}
                    className="w-full h-full object-cover group-hover:opacity-75 transition-opacity"
                    loading="lazy"
                  />
                ) : (
                  <div className="w-full h-full bg-gray-700 flex items-center justify-center text-sm text-gray-400">
                    無海報
                  </div>
                )}
                <div className="absolute top-2 right-2 px-2 py-1 bg-yellow-500 text-black text-sm font-bold rounded">
                  ⭐ {movie.rating.toFixed(1)}
                </div>
              </div>
              
              <div className="p-4">
                <h2 className="font-bold text-lg mb-2 group-hover:text-sky-400 transition-colors line-clamp-1">
                  {movie.title}
                </h2>
                <div className="text-sm text-gray-400 mb-2">
                  {new Date(movie.release_date).getFullYear()}
                </div>
                {movie.overview && (
                  <p className="text-sm text-gray-300 line-clamp-3">
                    {movie.overview}
                  </p>
                )}
              </div>
            </article>
          </Link>
        ))}
      </div>
    </div>
  )
}