'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { PageLayout } from '@/components/layouts';
import { MovieCard } from '@/components/MovieCard';
import { toMovieCardList } from '@/lib/movieAdapter';
import { movieExistsCache } from '@/lib/movieExistsCache';

export default function PopularPage() {
  const [movies, setMovies] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchPopularMovies();
  }, []);

  const fetchPopularMovies = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/popular/');
      const data = await response.json();
      const items = data.items || [];
      setMovies(items);
      
      // 🎯 優化：批量檢查所有電影是否在 DB
      const tmdbIds = items.map((m: any) => parseInt(m.id)).filter((id: number) => !isNaN(id));
      if (tmdbIds.length > 0) {
        // 批量檢查（並行請求，但有快取機制避免重複）
        await movieExistsCache.checkBatch(tmdbIds);
        console.log(`✅ 已批量檢查 ${tmdbIds.length} 部熱門電影`);
      }
    } catch (error) {
      console.error('獲取熱門電影失敗:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <PageLayout>
        <div className="flex flex-col justify-center items-center h-96 py-8">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full"
          />
          <p className="text-white text-xl mt-6">載入熱門電影中...</p>
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout>
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.5, ease: "easeOut" }}
        className="space-y-8 py-8"
      >
        {/* Page Title with Flame Effect */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-center"
        >
          <h1 className="text-5xl md:text-6xl font-bold mb-3
                       bg-gradient-to-r from-orange-400 via-red-500 to-pink-500
                       bg-clip-text text-transparent
                       drop-shadow-[0_0_30px_rgba(239,68,68,0.6)]
                       animate-pulse">
            熱門電影
          </h1>
          <p className="text-gray-400 text-sm md:text-base">
            現在最火紅的電影都在這裡
          </p>
        </motion.div>

        {/* Movies Grid */}
        {movies.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4 opacity-30">🎬</div>
            <p className="text-xl text-gray-400">目前沒有熱門電影資料</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {toMovieCardList(movies).map((movie, index) => (
              <motion.div
                key={movie.id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ 
                  duration: 0.4, 
                  delay: index * 0.05,
                  ease: [0.22, 1, 0.36, 1]
                }}
                className="relative"
              >
                {/* Ranking Badge */}
                {index < 10 && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: index * 0.05 + 0.3, type: "spring" }}
                    className="absolute -top-3 -left-3 z-30
                             w-12 h-12 rounded-full
                             bg-gradient-to-br from-yellow-400 to-orange-500
                             flex items-center justify-center
                             font-bold text-lg text-gray-900
                             shadow-lg shadow-yellow-500/50
                             border-2 border-yellow-300"
                  >
                    #{index + 1}
                  </motion.div>
                )}
                <MovieCard movie={movie} />
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </PageLayout>
  );
}
