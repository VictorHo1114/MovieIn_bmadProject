"use client";

import { useState, useEffect } from "react";

// 18個 mood labels - 從 backend/app/services/mapping_tables.py 取得
const MOOD_LABELS = [
  { id: "失戀", label: "失戀", category: "情緒", description: "心碎、需要療癒" },
  { id: "開心", label: "開心", category: "情緒", description: "想要歡笑、輕鬆愉快" },
  { id: "憂鬱", label: "憂鬱", category: "情緒", description: "情緒低落、需要共鳴" },
  { id: "想哭", label: "想哭", category: "情緒", description: "需要情緒宣洩" },
  { id: "興奮", label: "興奮", category: "情緒", description: "想要刺激、腎上腺素" },
  { id: "派對", label: "派對", category: "情境", description: "與朋友一起看、氣氛熱鬧" },
  { id: "獨自一人", label: "獨自一人", category: "情境", description: "一個人安靜觀賞" },
  { id: "約會", label: "約會", category: "情境", description: "浪漫氛圍、適合情侶" },
  { id: "家庭時光", label: "家庭時光", category: "情境", description: "全家一起看、老少咸宜" },
  { id: "認真觀影", label: "認真觀影", category: "觀影目的", description: "想要深度、藝術性" },
  { id: "感受經典", label: "感受經典", category: "觀影目的", description: "經典名作、影史地位" },
  { id: "放鬆腦袋", label: "放鬆腦袋", category: "觀影目的", description: "不用思考、純娛樂" },
  { id: "週末早晨", label: "週末早晨", category: "氛圍", description: "輕鬆愉快的早晨" },
  { id: "深夜觀影", label: "深夜觀影", category: "氛圍", description: "深夜觀影、神秘氛圍" },
  { id: "視覺饗宴", label: "視覺饗宴", category: "體驗", description: "震撼視覺、特效大片" },
  { id: "動作冒險", label: "動作冒險", category: "體驗", description: "刺激冒險、熱血沸騰" },
  { id: "腦洞大開", label: "腦洞大開", category: "體驗", description: "天馬行空、腦洞大開" },
  { id: "療癒", label: "療癒", category: "情緒", description: "需要安慰、溫暖治癒" }
];

interface MoodOrbitProps {
  selectedMoods: string[];
  onMoodsChange: (moods: string[]) => void;
}

export function MoodOrbit({ selectedMoods, onMoodsChange }: MoodOrbitProps) {
  // 響應式視窗寬度狀態
  const [viewportWidth, setViewportWidth] = useState(
    typeof window !== 'undefined' ? window.innerWidth : 1024
  );

  // 監聽視窗大小變化
  useEffect(() => {
    const handleResize = () => {
      setViewportWidth(window.innerWidth);
    };

    window.addEventListener('resize', handleResize);
    // 初始化時也觸發一次
    handleResize();

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 計算雙圈排列位置 - 真正的左右弧形分佈
  // 左側弧形：90° 到 270° (9點鐘到3點鐘，經過左側)
  // 右側弧形：270° 到 450° (3點鐘到9點鐘，經過右側) = -90° 到 90°
  // 避開：正上方 (-30° 到 30°) 和正下方 (150° 到 210°)
  
  const calculateDualCirclePosition = (index: number) => {
    // 響應式半徑 - 根據視窗寬度調整
    // Mobile (< 640px): 基礎半徑
    // Tablet (640-1024px): 中等半徑
    // Desktop (>= 1024px): 完整半徑
    
    let radiusScale = 1;
    if (viewportWidth < 480) {
      radiusScale = 0.32; // 超小手機: 32% 縮放
    } else if (viewportWidth < 640) {
      radiusScale = 0.42; // 手機: 42% 縮放
    } else if (viewportWidth < 1024) {
      radiusScale = 0.65; // 平板: 65% 縮放
    }
    
    const innerRadius = 380 * radiusScale;  // 內圈半徑（響應式）
    const outerRadius = 590 * radiusScale;  // 外圈半徑（響應式）
    
    // 允許擺放區域（用戶定義）：
    // 第一圈（內圈）- 右側 60°-150°，左側 210°-300°
    // 第二圈（外圈）- 右側 90°-150° (往內縮30°)，左側 210°-270° (往內縮30°)
    // 轉換到數學角度（-90°）：
    // 內圈 - 右側 -30°-60°，左側 120°-210°
    // 外圈 - 右側 0°-60°，左側 120°-180°
    
    if (index < 10) {
      // 第一圈（內圈）：10 個 labels
      // 右側 5 個：-30° 到 60° (90° 範圍)
      // 左側 5 個：120° 到 210° (90° 範圍)
      
      if (index < 5) {
        // 右側 5 個：-30°, -7.5°, 15°, 37.5°, 60°
        const angle = (-50 + (index * 22.5)) * Math.PI / 180;
        return {
          x: Math.cos(angle) * innerRadius,
          y: Math.sin(angle) * innerRadius,
        };
      } else {
        // 左側 5 個：120°, 142.5°, 165°, 187.5°, 210°
        const leftIndex = index - 5;
        const angle = (140 + (leftIndex * 22.5)) * Math.PI / 180;
        return {
          x: Math.cos(angle) * innerRadius,
          y: Math.sin(angle) * innerRadius,
        };
      }
    } else {
      // 第二圈（外圈）：8 個 labels
      // 右側 4 個：0° 到 60° (60° 範圍，往內縮30°)
      // 左側 4 個：120° 到 180° (60° 範圍，往內縮30°)
      
      const outerIndex = index - 10;
      
      if (outerIndex < 4) {
        // 右側 4 個：0°, 20°, 40°, 60°
        const angle = (-15 + (outerIndex * 12)) * Math.PI / 180;
        return {
          x: Math.cos(angle) * outerRadius,
          y: Math.sin(angle) * outerRadius,
        };
      } else {
        // 左側 4 個：120°, 140°, 160°, 180°
        const leftIndex = outerIndex - 4;
        const angle = (160 + (leftIndex * 12)) * Math.PI / 180;
        return {
          x: Math.cos(angle) * outerRadius,
          y: Math.sin(angle) * outerRadius,
        };
      }
    }
  };

  const toggleMood = (moodId: string) => {
    if (selectedMoods.includes(moodId)) {
      onMoodsChange(selectedMoods.filter(m => m !== moodId));
    } else {
      onMoodsChange([...selectedMoods, moodId]);
    }
  };

  return (
    <div className="absolute inset-0 pointer-events-none">
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        {/* Satellite-orbit labels: 12 inner (avoiding top/bottom) + 6 outer (left/right) */}
        {MOOD_LABELS.map((mood, index) => {
          const { x, y } = calculateDualCirclePosition(index);
          const isSelected = selectedMoods.includes(mood.id);
          
          return (
            <button
              key={mood.id}
              onClick={() => toggleMood(mood.id)}
              className={`absolute pointer-events-auto rounded-full 
                        px-2 py-1 sm:px-3 sm:py-1.5
                        text-[9px] sm:text-[10px] md:text-xs font-medium
                        transition-all duration-300 whitespace-nowrap group
                        min-h-[24px] sm:min-h-[28px] md:min-h-auto
                        ${isSelected 
                          ? 'bg-white/90 text-black scale-110 shadow-[0_0_30px_rgba(168,85,247,0.9)] border-2 border-purple-200' 
                          : 'bg-black/60 text-white/80 border border-white/30 hover:bg-white/10 hover:scale-105 hover:shadow-[0_0_20px_rgba(168,85,247,0.6)] hover:border-purple-400/50'
                        }`}
              style={{
                left: `${x}px`,
                top: `${y}px`,
                transform: 'translate(-50%, -50%)',
              }}
            >
              {mood.label}
              
              {/* Tooltip */}
              <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 
                            opacity-0 group-hover:opacity-100 transition-opacity duration-200
                            pointer-events-none z-50">
                <div className="bg-black/95 text-white text-xs px-3 py-2 rounded-lg
                              border border-white/30 whitespace-nowrap shadow-xl backdrop-blur-sm">
                  <div className="font-semibold text-white/90">{mood.category}</div>
                  <div className="text-gray-300">{mood.description}</div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
