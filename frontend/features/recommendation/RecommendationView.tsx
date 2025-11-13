"use client";

import { useState, useRef, useEffect, useCallback, memo } from "react";
import { motion } from "framer-motion";
import { BlackHoleCanvas } from "./BlackHoleCanvas";
import { MoodOrbit } from "./MoodOrbit";
import { FilterControls } from "./FilterControls";
import { MovieCard } from "@/components/MovieCard";
import { getSimpleRecommendations, type RecommendedMovie } from "./services";
import { StarField } from "./StarField";
import "./styles/recommendation.css";

export function RecommendationView() {
  const [selectedMoods, setSelectedMoods] = useState<string[]>([]);
  const [selectedEras, setSelectedEras] = useState<string[]>([]);
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [queryText, setQueryText] = useState<string>("");
  const [movies, setMovies] = useState<RecommendedMovie[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [strategy, setStrategy] = useState<string>("");
  const resultsRef = useRef<HTMLDivElement>(null);

  // 當 movies 更新時，自動滾動到結果區域（自定義滾動速度）
  useEffect(() => {
    if (movies.length > 0 && resultsRef.current) {
      // 延遲 300ms 再開始滾動，讓結果先渲染
      setTimeout(() => {
        const targetElement = resultsRef.current;
        if (!targetElement) return;

        const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        const duration = 1050; // 滾動持續時間（毫秒）- 調整這個值可以改變速度
        let start: number | null = null;

        // 緩動函數（easeInOutCubic）- 先加速再減速
        const easeInOutCubic = (t: number): number => {
          return t < 0.5 
            ? 4 * t * t * t 
            : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
        };

        const animation = (currentTime: number) => {
          if (start === null) start = currentTime;
          const timeElapsed = currentTime - start;
          const progress = Math.min(timeElapsed / duration, 1);
          const ease = easeInOutCubic(progress);
          
          window.scrollTo(0, startPosition + distance * ease);

          if (timeElapsed < duration) {
            requestAnimationFrame(animation);
          }
        };

        requestAnimationFrame(animation);
      }, 300);
    }
  }, [movies]);

  const handleGenerate = useCallback(async () => {
    // Phase 3.6: 移除強制選擇 mood 的限制，允許純自然語言查詢
    setIsLoading(true);
    try {
      const result = await getSimpleRecommendations(
        queryText, // 使用用戶輸入的自然語言
        selectedGenres,
        selectedMoods,
        selectedEras
      );
      setMovies(result.movies);
      setStrategy(result.strategy);
    } catch (error) {
      console.error("Failed to get recommendations:", error);
      alert("推薦失敗，請稍後再試");
    } finally {
      setIsLoading(false);
    }
  }, [selectedMoods, queryText, selectedGenres, selectedEras]);

  return (
    <div className="min-h-screen bg-black text-white relative flex flex-col">
      {/* Starry Background - 使用 Canvas 優化版本 */}
      <StarField />

      {/* Main Content */}
      <div className="flex-1">
        {/* Header - Removed for immersive experience */}

        {/* Main Section - BlackHole + Controls (響應式佈局) */}
        <div className="relative z-10 min-h-[calc(100vh-80px)] flex items-center justify-center px-4 lg:px-0 py-8 lg:py-0">
          
          {/* Mobile: 垂直佈局 */}
          <div className="flex flex-col items-center gap-8 lg:hidden w-full max-w-md">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="w-full flex flex-col gap-6 relative z-[200]"
            >
              <FilterControls
                selectedEras={selectedEras}
                selectedGenres={selectedGenres}
                onErasChange={setSelectedEras}
                onGenresChange={setSelectedGenres}
                gap="24px"
              />
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.7 }}
              >
                <textarea
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  placeholder="例如：我想看一部溫馨感人的家庭電影..."
                  className="w-full px-4 py-3 bg-black/80 border border-white/30 
                           rounded-lg text-white placeholder-gray-500 text-sm
                           focus:border-white/60 focus:outline-none focus:ring-1 focus:ring-white/40
                           focus:shadow-[0_0_15px_rgba(255,255,255,0.3)]
                           transition-all duration-200 resize-none backdrop-blur-sm"
                  rows={2}
                />
              </motion.div>
            </motion.div>
            
            <div className="relative w-full flex items-center justify-center py-8">
              <div className="relative">
                <BlackHoleCanvas onGenerate={handleGenerate} isLoading={isLoading} />
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.8, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  className="absolute inset-0 pointer-events-none overflow-visible"
                >
                  <MoodOrbit 
                    selectedMoods={selectedMoods} 
                    onMoodsChange={setSelectedMoods} 
                  />
                </motion.div>
              </div>
            </div>
          </div>

          {/* Desktop: 置中黑洞，下方控制面板 */}
          <div className="hidden lg:block relative">
            {/* 黑洞 + Mood Orbit - 水平居中 */}
            <div className="relative flex items-center justify-center py-8">
              <div className="relative">
                <BlackHoleCanvas onGenerate={handleGenerate} isLoading={isLoading} />
                
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.8, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  className="absolute inset-0 pointer-events-none overflow-visible"
                >
                  <MoodOrbit 
                    selectedMoods={selectedMoods} 
                    onMoodsChange={setSelectedMoods} 
                  />
                </motion.div>
              </div>
            </div>

            {/* 控制面板 - 絕對定位在黑洞下方中央 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="absolute top-full left-1/2 -translate-x-1/2 -mt-26 flex flex-col gap-4 scale-90 origin-top z-[200]"
              style={{ width: '350px' }}
            >
              <FilterControls
                selectedEras={selectedEras}
                selectedGenres={selectedGenres}
                onErasChange={setSelectedEras}
                onGenresChange={setSelectedGenres}
                gap="16px"
              />
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.7 }}
              >
                <textarea
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  placeholder="例如：我想看一部溫馨感人的家庭電影..."
                  className="w-full px-3 py-1.5 bg-black/80 border border-white/30 
                           rounded-full text-white placeholder-gray-500 text-xs
                           focus:border-white/60 focus:outline-none focus:ring-1 focus:ring-white/40
                           focus:shadow-[0_0_15px_rgba(255,255,255,0.3)]
                           transition-all duration-200 resize-none backdrop-blur-sm"
                  rows={1}
                />
              </motion.div>
            </motion.div>
          </div>
        </div>

      {/* Results Grid */}
      {movies.length > 0 && (
        <motion.div 
          ref={resultsRef} 
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="py-12 px-4 relative z-10"
        >
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-3xl font-bold text-center mb-8 text-white/90"
          >
            為你推薦
          </motion.h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 
                        gap-6 max-w-7xl mx-auto">
            {movies.map((movie, index) => (
              <motion.div
                key={movie.id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ 
                  duration: 0.5, 
                  delay: index * 0.05,
                  ease: [0.22, 1, 0.36, 1]
                }}
              >
                <MovieCard movie={movie} />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      </div>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/10 py-6 mt-auto">
        <div className="text-center">
          <p className="text-gray-500 text-sm">
            © 2025 MovieIn. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
