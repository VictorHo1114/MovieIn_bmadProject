"use client";

import { useState, useRef, useEffect, useCallback, memo } from "react";
import { motion } from "framer-motion";
import { BlackHoleCanvas } from "./BlackHoleCanvas";
import { MoodOrbit } from "./MoodOrbit";
import { FilterControls } from "./FilterControls";
import { MovieCard } from "@/components/MovieCard";
import { getSimpleRecommendations, type RecommendedMovie } from "./services";

// 🎨 控制面板位置配置
// 視覺平衡原則：上下留白，左右豐富
const CONTROL_PANEL_CONFIG = {
  left: "530px",     // 距離左邊距離
  top: "400px",      // 距離頂部距離
  width: "180px",    // 面板寬度
  gap: "40px"         // 年代與類型之間的間隔
};

// 🎨 文字輸入框位置配置
const TEXTAREA_CONFIG = {
  left: "480px",     // 距離左邊距離
  top: "550px",      // 距離頂部距離
  width: "280px",    // 輸入框寬度
  height: "35px"     // 輸入框高度
};

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
    if (selectedMoods.length === 0) {
      alert("請至少選擇一個心情標籤");
      return;
    }

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
      {/* Starry Background */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.5, ease: "easeOut" }}
        className="fixed inset-0 overflow-hidden pointer-events-none bg-black"
      >
        <div className="stars-layer"></div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1">
        {/* Header - Removed for immersive experience */}

        {/* Main Section - BlackHole + MoodOrbit */}
        <div className="relative flex justify-center items-center z-10" 
             style={{ 
               height: 'calc(100vh - 80px)', 
               maxHeight: 'calc(100vh - 80px)',
               marginLeft: '-60px',  // 給左側控制板騰出空間
               paddingLeft: '60px'   // 保持內容居中
             }}>
          {/* BlackHole Canvas - No animation wrapper */}
          <BlackHoleCanvas onGenerate={handleGenerate} isLoading={isLoading} />
          
          {/* Mood Orbit Labels - Fade in with delay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
          >
            <MoodOrbit 
              selectedMoods={selectedMoods} 
              onMoodsChange={setSelectedMoods} 
            />
          </motion.div>

          {/* Filter Controls - Configurable Position */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="absolute z-20"
            style={{
              left: CONTROL_PANEL_CONFIG.left,
              top: CONTROL_PANEL_CONFIG.top,
              width: CONTROL_PANEL_CONFIG.width,
              display: 'flex',
              flexDirection: 'column',
              gap: CONTROL_PANEL_CONFIG.gap
            }}
          >
            {/* Dropdowns */}
            <FilterControls
              selectedEras={selectedEras}
              selectedGenres={selectedGenres}
              onErasChange={setSelectedEras}
              onGenresChange={setSelectedGenres}
              gap={CONTROL_PANEL_CONFIG.gap}
            />
          </motion.div>
            
          {/* Natural Language Input - Separate Position */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="absolute z-20"
            style={{
              left: TEXTAREA_CONFIG.left,
              top: TEXTAREA_CONFIG.top,
              width: TEXTAREA_CONFIG.width
            }}
          >
            <textarea
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="例如：我想看一部溫馨感人的家庭電影..."
              className="w-full px-3 py-2 bg-black/80 border border-white/30 
                       rounded-lg text-white placeholder-gray-500 text-xs
                       focus:border-white/60 focus:outline-none focus:ring-1 focus:ring-white/40
                       focus:shadow-[0_0_15px_rgba(255,255,255,0.3)]
                       transition-all duration-200 resize-none backdrop-blur-sm"
              style={{ height: TEXTAREA_CONFIG.height }}
            />
          </motion.div>
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
