'use client'; 

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import Slider from 'react-slick'; 
import { PageLayout } from '@/components/layouts';
import { MovieCard } from '@/components/MovieCard';
import { Api, type FrontendMovie } from '@/lib/api';
import { movieExistsCache } from '@/lib/movieExistsCache';

// 將 FrontendMovie 轉換為 RecommendedMovie 格式
function toRecommendedMovie(movie: FrontendMovie) {
  return {
    id: movie.id.toString(),
    title: movie.title,
    overview: movie.overview,
    poster_url: movie.poster_url || '',
    vote_average: movie.vote_average,
    release_year: movie.release_year ?? undefined,
  };
}

// 這是 react-slick 需要的設定
const sliderSettings = {
  dots: true,
  infinite: true,
  speed: 500,
  slidesToShow: 1,
  slidesToScroll: 1,
  autoplay: true,
  arrows: true,
};

export function HomeFeed() {
  const [randomMovies, setRandomMovies] = useState<FrontendMovie[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRandomMovies();
  }, []);

  const fetchRandomMovies = async () => {
    try {
      setIsLoading(true);
      const movies = await Api.movies.getRandom(4); // 只獲取 4 部電影
      setRandomMovies(movies);
      
      // 🎯 優化：預先標記這些電影為存在於 DB（來自 DB 的隨機電影）
      const tmdbIds = movies.map(m => m.id);
      movieExistsCache.markAsExists(tmdbIds);
      
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch random movies:', err);
      setError('載入電影失敗，請稍後再試');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <PageLayout>
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.5, ease: "easeOut" }}
        className="space-y-8 py-8"
      >
        {/* 頂部輪播 (Slick Slider) */}
        <div className="w-full mb-8">
          <Slider {...sliderSettings}>
            <div>
              <img src="/img/slider1.jpg" className="w-full rounded-lg" alt="Slider 1" />
            </div>
            <div>
              <img src="/img/slider2.jpg" className="w-full rounded-lg" alt="Slider 2" />
            </div>
            <div>
              <img src="/img/slider3.jpg" className="w-full rounded-lg" alt="Slider 3" />
            </div>
          </Slider>
        </div>

        {/* Page Title */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-center"
        >
          <h1 className="text-5xl md:text-6xl font-bold mb-3
                       bg-gradient-to-r from-purple-400 via-pink-500 to-red-500
                       bg-clip-text text-transparent
                       drop-shadow-[0_0_30px_rgba(168,85,247,0.6)]">
            隨機推薦
          </h1>
          <p className="text-gray-400 text-sm md:text-base">
            從資料庫隨機挑選的精選電影
          </p>
        </motion.div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col justify-center items-center py-20">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full"
            />
            <p className="text-white text-xl mt-6">載入推薦電影中...</p>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="text-center py-20">
            <p className="text-xl text-red-400 mb-4">{error}</p>
            <button
              onClick={fetchRandomMovies}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              重試
            </button>
          </div>
        )}

        {/* Movies Grid */}
        {!isLoading && !error && randomMovies.length === 0 && (
          <div className="text-center py-20">
            <div className="text-6xl mb-4 opacity-30">🎬</div>
            <p className="text-xl text-gray-400">目前沒有電影資料</p>
          </div>
        )}

        {!isLoading && !error && randomMovies.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {randomMovies.map((movie, index) => (
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
                <MovieCard 
                  movie={toRecommendedMovie(movie)}
                  // 移除 callbacks - 依賴 movieListStore 的觀察者模式自動更新
                />
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </PageLayout>
  );
}