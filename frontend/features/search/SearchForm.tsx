'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { API_BASE } from '@/lib/config'
import type { SearchResult } from '@/lib/types'
import { MovieCard } from '@/components/MovieCard'
import { toMovieCardList } from '@/lib/movieAdapter'
import { movieExistsCache } from '@/lib/movieExistsCache'

function SearchFormContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const initialQuery = searchParams.get('q') || ''
  
  const [q, setQ] = useState(initialQuery)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SearchResult | null>(null)

  // 當 URL 中的查詢參數改變時，更新搜尋結果
  useEffect(() => {
    if (initialQuery) {
      doSearch(initialQuery)
    }
  }, [initialQuery])

  async function doSearch(query: string) {
    if (!query) {
      setResult(null)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`)
      if (!res.ok) throw new Error(`Status ${res.status}`)
      const data = (await res.json()) as SearchResult
      setResult(data)
      
      // 🎯 優化：批量檢查搜尋結果中的電影是否在 DB
      if (data.items && data.items.length > 0) {
        const tmdbIds = data.items
          .map((m: any) => parseInt(m.id))
          .filter((id: number) => !isNaN(id));
        
        if (tmdbIds.length > 0) {
          await movieExistsCache.checkBatch(tmdbIds);
          console.log(`✅ 已批量檢查 ${tmdbIds.length} 部搜尋結果電影`);
        }
      }
    } catch (e: any) {
      setError(e?.message ?? 'Unknown error')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    // 更新 URL，保持搜尋狀態
    router.push(`/search?q=${encodeURIComponent(q)}`)
  }

  return (
    <div>
      {/* Search Bar - Cosmic Style */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-3xl mx-auto mb-12"
      >
        <form onSubmit={onSubmit} className="relative">
          <input
            aria-label="Search movies"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="搜尋電影名稱、導演、演員..."
            className="w-full px-6 py-4 pr-32 rounded-xl
                     bg-black/50 border-2 border-purple-500/30
                     text-white placeholder-gray-500
                     focus:border-purple-500 focus:outline-none
                     focus:ring-2 focus:ring-purple-500/50
                     focus:shadow-[0_0_30px_rgba(168,85,247,0.3)]
                     transition-all duration-300
                     backdrop-blur-sm"
          />
          <button
            type="submit"
            className="absolute right-2 top-1/2 -translate-y-1/2
                     px-6 py-2 bg-purple-600 hover:bg-purple-700
                     rounded-lg text-white font-medium
                     transition-all duration-300
                     hover:shadow-lg hover:shadow-purple-500/50
                     disabled:bg-gray-600 disabled:cursor-not-allowed"
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                搜尋中
              </span>
            ) : (
              '🔍 搜尋'
            )}
          </button>
        </form>
      </motion.div>

      {/* Error Message */}
      {error && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center mb-8"
        >
          <div className="inline-block px-6 py-3 bg-red-500/20 border border-red-500/50 rounded-lg">
            <p className="text-red-400">❌ 搜尋失敗: {error}</p>
          </div>
        </motion.div>
      )}

      {/* Search Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          {result.items.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-6xl mb-4">🎬</div>
              <h3 className="text-2xl font-bold text-gray-400 mb-2">沒有找到相關電影</h3>
              <p className="text-gray-500">試試不同的關鍵字</p>
            </div>
          ) : (
            <>
              {/* Results Count */}
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8"
              >
                <p className="text-lg text-gray-300">
                  找到 <span className="font-bold text-purple-400 text-2xl">{result.items.length}</span> 部電影
                </p>
              </motion.div>

              {/* Movie Grid - Using Unified MovieCard */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {toMovieCardList(result.items).map((movie, index) => (
                  <motion.div
                    key={movie.id}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ 
                      duration: 0.4, 
                      delay: index * 0.05,
                      ease: [0.22, 1, 0.36, 1]
                    }}
                  >
                    <MovieCard movie={movie} />
                  </motion.div>
                ))}
              </div>
            </>
          )}
        </motion.div>
      )}

      {/* Initial Empty State */}
      {!loading && !result && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <div className="text-8xl mb-6 opacity-20">🔭</div>
          <h3 className="text-xl text-gray-400 mb-2">在宇宙中探索電影</h3>
          <p className="text-gray-600">輸入關鍵字開始搜尋</p>
        </motion.div>
      )}
    </div>
  )
}

export default function SearchForm() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">載入搜尋中...</p>
        </div>
      </div>
    }>
      <SearchFormContent />
    </Suspense>
  )
}
