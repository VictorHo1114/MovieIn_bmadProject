'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { MovieCard } from '@/components/MovieCard';
import { Api, type WatchlistItem } from '@/lib/api';
import { movieListStore } from '@/lib/movieListStore';
import { movieExistsCache } from '@/lib/movieExistsCache';

// 將 WatchlistItem 轉換為 MovieCard 需要的格式
function toRecommendedMovie(item: WatchlistItem) {
  return {
    id: item.movie.id.toString(),
    title: item.movie.title,
    overview: item.movie.overview,
    poster_url: item.movie.poster_url || '',
    vote_average: item.movie.vote_average,
    release_year: item.movie.release_year ?? undefined,
  };
}

export function WatchlistSection() {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWatchlist();
    
    // 訂閱 store 變化，使用本地過濾而非重新載入
    const unsubscribe = movieListStore.subscribe(() => {
      // 只更新本地狀態，過濾掉已移除的電影
      setWatchlist(prevList => 
        prevList.filter(item => 
          movieListStore.isInWatchlist(item.movie.id)
        )
      );
    });
    
    return unsubscribe;
  }, []);

  const fetchWatchlist = async () => {
    try {
      setIsLoading(true);
      const data = await Api.watchlist.getAll();
      setWatchlist(data.items);
      
      // 🎯 優化：預先標記這些電影為存在於 DB（避免每個 MovieCard 重複檢查）
      const tmdbIds = data.items.map(item => item.movie.id);
      movieExistsCache.markAsExists(tmdbIds);
      
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch watchlist:', err);
      setError('載入待看清單失敗');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col justify-center items-center py-20">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full"
        />
        <p className="text-gray-600 text-lg mt-4">載入中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={fetchWatchlist}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          重試
        </button>
      </div>
    );
  }

  if (watchlist.length === 0) {
    return (
      <div className="text-center py-20">
        <div className="text-6xl mb-4 opacity-30">📋</div>
        <p className="text-xl text-gray-600 mb-2">你的待看清單是空的</p>
        <p className="text-sm text-gray-400">
          點擊電影卡片的「加入 Watchlist」按鈕來新增電影
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          待看清單 <span className="text-purple-600">({watchlist.length})</span>
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          管理你想看的電影
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {watchlist.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
          >
            <MovieCard 
              movie={toRecommendedMovie(item)}
              // 不需要 callbacks - movieListStore 會自動觸發訂閱更新
            />
          </motion.div>
        ))}
      </div>
    </div>
  );
}
