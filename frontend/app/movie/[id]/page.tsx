'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { API_BASE } from '@/lib/config'

interface MovieDetail {
  id: string
  title: string
  original_title: string
  overview: string | null
  release_date: string
  rating: number
  vote_count: number
  runtime: number | null
  poster_url: string | null
  backdrop_url: string | null
}

export default function MovieDetailPage() {
  const params = useParams()
  const movieId = params?.id as string
  const [movie, setMovie] = useState<MovieDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!movieId) return

    async function fetchMovie() {
      try {
        const res = await fetch(`${API_BASE}/movie/${movieId}`)
        if (!res.ok) {
          if (res.status === 404) {
            throw new Error('找不到此電影')
          }
          throw new Error(`電影載入失敗：Status ${res.status}`)
        }
        const data = await res.json()
        setMovie(data)
      } catch (e: any) {
        setError(e?.message ?? '載入失敗')
      } finally {
        setLoading(false)
      }
    }
    fetchMovie()
  }, [movieId])

  if (loading) return <div className="p-6">載入中...</div>
  if (error) return <div className="p-6 text-red-500">錯誤: {error}</div>
  if (!movie) return <div className="p-6">找不到此電影</div>

  return (
    <div className="min-h-screen bg-gray-900">
      {/* 背景圖 */}
      {movie.backdrop_url && (
        <div 
          className="absolute top-0 left-0 w-full h-[50vh] bg-cover bg-center opacity-20"
          style={{ backgroundImage: `url(${movie.backdrop_url})` }}
        />
      )}

      {/* 主要內容 */}
      <div className="relative container mx-auto px-4 py-8">
        {/* 返回按鈕 */}
        <button
          onClick={() => window.history.back()}
          className="inline-flex items-center gap-2 mb-6 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-lg transition-all hover:scale-105"
        >
          <span className="text-xl">←</span>
          <span>返回上一頁</span>
        </button>

        <div className="flex flex-col md:flex-row gap-8">
          {/* 海報 */}
          <div className="w-full md:w-1/3">
            {movie.poster_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={movie.poster_url}
                alt={movie.title}
                className="w-full rounded-lg shadow-xl"
              />
            ) : (
              <div className="w-full aspect-[2/3] bg-gray-700 rounded-lg flex items-center justify-center text-white">
                無海報
              </div>
            )}
          </div>

          {/* 電影資訊 */}
          <div className="flex-1">
            <h1 className="text-4xl font-bold mb-2 text-white">{movie.title}</h1>
            
            {movie.original_title !== movie.title && (
              <h2 className="text-xl text-gray-200 mb-4">{movie.original_title}</h2>
            )}

            <div className="mb-6">
              <div className="text-lg mb-2 text-yellow-400 font-medium">
                ⭐ {movie.rating.toFixed(1)} <span className="text-gray-200">({movie.vote_count} 投票)</span>
              </div>
              <div className="text-gray-200">
                {movie.release_date?.split('-')[0]}
                {movie.runtime && ` • ${movie.runtime} 分鐘`}
              </div>
            </div>

            {movie.overview && (
              <div className="mb-8">
                <h3 className="text-xl font-semibold mb-2 text-white">劇情簡介</h3>
                <p className="text-gray-100 leading-relaxed bg-black/30 p-4 rounded-lg">{movie.overview}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}