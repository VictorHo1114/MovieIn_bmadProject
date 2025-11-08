'use client'
import { useState } from 'react'
import { API_BASE } from '@/lib/config'
import type { SearchResult } from '@/lib/types'

export default function SearchForm() {
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SearchResult | null>(null)

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
    await doSearch(q)
  }

  return (
    <div>
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

      {error && <div className="text-red-400 mb-2">Error: {error}</div>}

      {result && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mt-2">
          {result.items.map((m) => {
            const img = m.poster_url ?? (m.poster_path ? `https://image.tmdb.org/t/p/w300${m.poster_path}` : null)
            return (
              <article key={m.id} className="border rounded p-3 bg-white/5 flex flex-col group hover:bg-white/10 transition-colors cursor-pointer">
                <a href={`/movie/${m.id}`} className="flex flex-col flex-1">
                  {img ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={img} alt={m.title} className="w-full h-44 object-cover rounded mb-2 group-hover:opacity-80 transition-opacity" />
                  ) : (
                    <div className="w-full h-44 bg-gray-200 mb-2 rounded flex items-center justify-center text-sm text-gray-500">No image</div>
                  )}
                  <div className="text-sm opacity-70">{m.year}</div>
                  <div className="font-semibold group-hover:text-sky-400 transition-colors">{m.title}</div>
                  <div className="text-xs opacity-70">⭐ {m.rating ?? 'N/A'}</div>
                  {m.overview && <p className="text-sm opacity-70 mt-2 line-clamp-3">{m.overview}</p>}
                </a>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
