'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { API_BASE } from '@/lib/config'
import type { SearchResult } from '@/lib/types'

export default function SearchForm() {
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
      <div className="max-w-2xl mx-auto mb-6">
        <form onSubmit={onSubmit} className="flex gap-2 items-center mb-4">
          <input
            aria-label="Search movies"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search movies, e.g. Titanic"
            className="flex-1 rounded px-3 py-2 bg-white text-black border border-gray-300 placeholder:opacity-60"
          />
        <button
          type="submit"
          className="px-3 py-2 bg-sky-500 hover:bg-sky-600 rounded text-white"
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      </div>

      {error && <div className="text-red-400 mb-2">Error: {error}</div>}

      {result && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8 mt-6">
          {result.items.map((m) => {
            const img = m.poster_url ?? (m.poster_path ? `https://image.tmdb.org/t/p/w500${m.poster_path}` : null)
            return (
              <a key={m.id} href={`/movie/${m.id}`} className="group">
                <article className="bg-gray-800 rounded-2xl overflow-hidden shadow-xl hover:shadow-yellow-400/40 transition-all duration-300 hover:-translate-y-1 border border-gray-700">
                  <div className="relative aspect-[2/3]">
                    {img ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img 
                        src={img} 
                        alt={m.title} 
                        className="w-full h-full object-cover group-hover:opacity-80 transition-opacity" 
                        loading="lazy"
                      />
                    ) : (
                      <div className="w-full h-full bg-gray-700 flex items-center justify-center text-base text-gray-300">
                        無海報
                      </div>
                    )}
                    <div className="absolute top-2 right-2 px-2 py-1 bg-yellow-400 text-gray-900 text-sm font-bold rounded shadow">
                      ⭐ {m.rating ?? 'N/A'}
                    </div>
                  </div>
                  <div className="p-4">
                    <h2 className="font-bold text-lg mb-2 text-white group-hover:text-yellow-300 transition-colors line-clamp-1">
                      {m.title}
                    </h2>
                    <div className="text-sm text-gray-300 mb-2">
                      {m.year}
                    </div>
                    {m.overview && (
                      <p className="text-sm text-gray-200 line-clamp-3">
                        {m.overview}
                      </p>
                    )}
                  </div>
                </article>
              </a>
            )
          })}
        </div>
      )}
    </div>
  )
}
