# Phase 3.6 前端整合指南

## 🎯 概述

Phase 3.6 Embedding-First 推薦系統已完全整合到現有 API，前端可以透過一個參數開關來使用新架構。

---

## ✅ 已完成的後端整合

### 1. API Endpoint 擴展

**路徑**: `POST /api/recommend/v2/movies`

**新增參數**:
```typescript
{
  query: string;
  selected_genres: string[];
  selected_moods: string[];
  selected_eras: string[];
  randomness: number;
  decision_threshold: number;
  use_legacy: boolean;
  use_phase36: boolean;  // ⭐ 新增：啟用 Phase 3.6
}
```

### 2. 返回格式擴展

**Phase 3.6 返回值**:
```typescript
{
  success: true,
  query: string,
  count: number,
  movies: [
    {
      id: string,
      title: string,
      overview: string,
      poster_url: string,
      vote_average: number,
      // ⭐ Phase 3.6 新增欄位
      embedding_score: number,    // 0.0-1.0 語義相似度
      match_ratio: number,         // 0.0-1.0 特徵匹配率
      final_score: number,         // 綜合評分
      quadrant: string,            // "q1_perfect_match" | "q2_semantic_discovery" | "q4_fallback"
      // 原有欄位
      release_date: string,
      genres: string[],
      keywords: string[],
      mood_tags: string[]
    }
  ],
  strategy: "Phase36-EmbeddingFirst",
  version: "3.6",
  config: {
    architecture: "Embedding-First",
    primary_engine: "Embedding Similarity Search",
    secondary_engine: "Feature Filtering",
    quadrants: 3
  }
}
```

---

## 🚀 前端使用方式

### 方式 1: 簡單開關（推薦）

```typescript
// frontend/features/recommendation/RecommendationView.tsx

import { getSimpleRecommendations } from "./services";

const RecommendationView = () => {
  const [usePhase36, setUsePhase36] = useState(false);  // 新增狀態
  
  const handleSearch = async () => {
    const result = await getSimpleRecommendations(
      query,
      selectedGenres,
      selectedMoods,
      selectedEras,
      usePhase36  // 傳遞 Phase 3.6 開關
    );
    
    console.log("Strategy:", result.strategy);  // "Phase36-EmbeddingFirst" 或 "Feature"/"Embedding"
    console.log("Version:", result.version);    // "3.6" 或 undefined
    setMovies(result.movies);
  };
  
  return (
    <div>
      {/* Phase 3.6 開關（可選，用於 A/B 測試） */}
      <label>
        <input
          type="checkbox"
          checked={usePhase36}
          onChange={(e) => setUsePhase36(e.target.checked)}
        />
        使用 Phase 3.6 Embedding-First 架構
      </label>
      
      {/* 搜尋按鈕 */}
      <button onClick={handleSearch}>搜尋電影</button>
      
      {/* 顯示結果 */}
      {movies.map(movie => (
        <MovieCard 
          key={movie.id} 
          movie={movie}
          showPhase36Info={usePhase36}  // 顯示 Phase 3.6 資訊
        />
      ))}
    </div>
  );
};
```

### 方式 2: 自動啟用（生產環境）

```typescript
// 直接啟用 Phase 3.6，不需要開關
const result = await getSimpleRecommendations(
  query,
  selectedGenres,
  selectedMoods,
  selectedEras,
  true  // 直接啟用 Phase 3.6
);
```

---

## 📊 顯示 Phase 3.6 資訊（可選）

### 電影卡片增強

```typescript
// frontend/components/MovieCard.tsx

interface MovieCardProps {
  movie: RecommendedMovie;
  showPhase36Info?: boolean;
}

const MovieCard = ({ movie, showPhase36Info }: MovieCardProps) => {
  return (
    <div className="movie-card">
      <img src={movie.poster_url} alt={movie.title} />
      <h3>{movie.title}</h3>
      <p>評分: {movie.vote_average}/10</p>
      
      {/* Phase 3.6 額外資訊 */}
      {showPhase36Info && movie.quadrant && (
        <div className="phase36-info">
          <div className="quadrant-badge">
            {movie.quadrant === "q1_perfect_match" && "🎯 完美匹配"}
            {movie.quadrant === "q2_semantic_discovery" && "🔍 語義發現"}
            {movie.quadrant === "q4_fallback" && "📚 候補推薦"}
          </div>
          <div className="scores">
            <span>語義: {(movie.embedding_score * 100).toFixed(0)}%</span>
            <span>匹配: {(movie.match_ratio * 100).toFixed(0)}%</span>
            <span>綜合: {movie.final_score.toFixed(1)}</span>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## 🎨 UI 建議（可選）

### 1. 象限徽章樣式

```css
/* styles/phase36.css */

.quadrant-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}

.quadrant-badge.q1_perfect_match {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.quadrant-badge.q2_semantic_discovery {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.quadrant-badge.q4_fallback {
  background: #e0e7ff;
  color: #4c51bf;
}
```

### 2. 分數顯示

```typescript
// components/ScoreDisplay.tsx

const ScoreDisplay = ({ movie }: { movie: RecommendedMovie }) => {
  if (!movie.embedding_score) return null;
  
  return (
    <div className="score-bars">
      <div className="score-item">
        <label>語義相似度</label>
        <div className="progress-bar">
          <div 
            className="progress-fill embedding" 
            style={{ width: `${movie.embedding_score * 100}%` }}
          />
        </div>
        <span>{(movie.embedding_score * 100).toFixed(0)}%</span>
      </div>
      
      <div className="score-item">
        <label>特徵匹配率</label>
        <div className="progress-bar">
          <div 
            className="progress-fill match" 
            style={{ width: `${movie.match_ratio * 100}%` }}
          />
        </div>
        <span>{(movie.match_ratio * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
};
```

---

## 🧪 A/B 測試建議

### 1. 功能旗標方式

```typescript
// lib/featureFlags.ts

export const FEATURE_FLAGS = {
  PHASE_36_ENABLED: process.env.NEXT_PUBLIC_PHASE36_ENABLED === 'true',
  SHOW_PHASE36_UI: process.env.NEXT_PUBLIC_SHOW_PHASE36_UI === 'true',
};

// 使用
const usePhase36 = FEATURE_FLAGS.PHASE_36_ENABLED;
```

### 2. 用戶分組測試

```typescript
// lib/abTest.ts

export function shouldUsePhase36(userId: string): boolean {
  // 50% 用戶使用 Phase 3.6
  const hash = hashCode(userId);
  return hash % 2 === 0;
}

function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash = hash & hash;
  }
  return Math.abs(hash);
}
```

---

## 📝 最小變更方案（無 UI 改動）

如果不想修改 UI，只需要修改 `services.ts`：

```typescript
// frontend/features/recommendation/services.ts

export async function getSimpleRecommendations(
  query: string,
  genres: string[],
  moods: string[],
  eras: string[]
): Promise<{ movies: RecommendedMovie[]; strategy: string }> {
  const response = await fetch("http://localhost:8000/api/recommend/v2/movies", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      selected_genres: genres,
      selected_moods: moods,
      selected_eras: eras,
      use_phase36: true,  // 直接啟用 Phase 3.6 ⭐
    }),
  });

  const data = await response.json();
  return {
    movies: data.movies || [],
    strategy: data.strategy || "",
  };
}
```

**這樣前端完全不需要其他改動，後端自動使用 Phase 3.6！** ✅

---

## 🔄 版本切換策略

### 策略 1: 漸進式灰度發布（推薦）

```typescript
// 階段 1: 10% 用戶
const usePhase36 = Math.random() < 0.1;

// 階段 2: 50% 用戶
const usePhase36 = Math.random() < 0.5;

// 階段 3: 100% 用戶
const usePhase36 = true;
```

### 策略 2: 基於場景切換

```typescript
// 複雜查詢使用 Phase 3.6
const usePhase36 = query.length > 20 || moods.length > 2;

// 簡單查詢使用 Phase 3.5
const usePhase36 = false;
```

### 策略 3: 手動切換（開發/測試）

```typescript
// 環境變數控制
const usePhase36 = process.env.NEXT_PUBLIC_USE_PHASE36 === 'true';
```

---

## ✅ 檢查清單

### 後端整合 ✅
- [x] API endpoint 新增 `use_phase36` 參數
- [x] 返回格式包含 Phase 3.6 欄位
- [x] `recommend_movies_embedding_first()` 函數可用
- [x] 所有測試通過 (32/32)

### 前端整合
- [x] `services.ts` 新增 `usePhase36` 參數
- [x] TypeScript 介面更新（新增 `embedding_score`, `quadrant` 等）
- [ ] （可選）UI 顯示象限資訊
- [ ] （可選）UI 顯示分數細節
- [ ] （可選）A/B 測試實現

---

## 🚀 快速啟動

### 1. 最簡單方式（無 UI 改動）

修改 `frontend/features/recommendation/services.ts` 第 23 行：

```typescript
use_phase36: true,  // 啟用 Phase 3.6
```

重啟前端即可！

### 2. 帶開關方式（可控測試）

修改 `frontend/features/recommendation/RecommendationView.tsx`：

```typescript
// 新增狀態
const [usePhase36, setUsePhase36] = useState(true);

// 傳遞參數
const result = await getSimpleRecommendations(
  query, genres, moods, eras, usePhase36
);
```

---

## 📞 技術支援

- **API 文檔**: `/api/recommend/v2/system-info`
- **測試檔案**: `backend/test_phase36_integration.py`
- **配置檔案**: `backend/app/services/phase36_config.py`

---

**文檔版本**: 1.0  
**最後更新**: 2025-11-14  
**狀態**: ✅ 前端整合完成，隨時可用
