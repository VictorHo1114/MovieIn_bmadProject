# MovieIn 電影推薦系統 UI/UX 規格文件

**版本**: 1.0  
**最後更新**: 2025-11-09  
**負責人**: UX Expert (Sally)

---

## 1. Introduction

本文檔定義 **MovieIn 電影推薦系統** 的使用者體驗目標、資訊架構、使用者流程和視覺設計規格，為視覺設計和前端開發提供基礎，確保一致且以使用者為中心的體驗。

### 1.1 Overall UX Goals & Principles

#### Target User Personas

1. **電影探索者 (Movie Explorer)**
   - 年齡：18-35歲
   - 特徵：希望透過心情找到完美的電影，享受視覺化的探索過程
   - 痛點：傳統推薦系統太理性，缺乏情感連結

2. **快速決策者 (Quick Decider)**
   - 年齡：25-45歲
   - 特徵：忙碌的觀眾，需要快速篩選符合特定類型和年代的電影
   - 痛點：選擇過載，需要精準篩選工具

3. **沉浸式體驗愛好者 (Experience Seeker)**
   - 年齡：20-40歲
   - 特徵：重視 UI/UX 美學，享受具有動畫和互動感的介面
   - 痛點：大多數推薦系統介面單調乏味

#### Usability Goals

- **視覺吸引力**: 黑洞主題提供令人難忘的視覺體驗，讓推薦過程本身成為享受
- **直覺互動**: Mood labels 環繞黑洞的設計讓選擇過程自然流暢
- **即時回饋**: 所有互動（hover、selection、generation）都有明確的視覺反饋
- **流暢轉場**: 從選擇到推薦結果的兩段式 UI 轉場自然且有動畫感
- **效率優先**: 核心推薦流程 < 30 秒完成

#### Design Principles

1. **視覺先行 (Visual First)** - 用視覺敘事代替文字說明，讓介面本身就是體驗
2. **宇宙美學 (Cosmic Aesthetic)** - 黑洞、星空、漸層光效營造沉浸式的宇宙氛圍
3. **互動即探索 (Interaction as Discovery)** - 每個 hover 和 click 都揭示新的可能性
4. **流暢動畫 (Fluid Animation)** - 所有轉場和微互動都使用 60fps 流暢動畫
5. **心情優先 (Mood-First)** - Mood labels 是核心交互，其他篩選為輔助

---

## 2. Information Architecture

### 2.1 Site Map / Screen Inventory

\\\mermaid
graph TD
    A[推薦主畫面 Recommendation View] --> B[狀態1: 選擇階段]
    A --> C[狀態2: 結果階段]
    
    B --> B1[黑洞動畫區 800x800px]
    B --> B2[Mood 環繞圈 18 labels radius=450px]
    B --> B3[篩選控制區]
    B --> B4[自然語言輸入]
    
    B1 --> B1a[GENERATE 按鈕]
    B3 --> B3a[年代選擇器 7 options]
    B3 --> B3b[類型選擇器 19 options]
    
    C --> C1[推薦策略提示]
    C --> C2[電影網格 10 cards]
    
    C2 --> C2a[Movie Card 正面]
    C2 --> C2b[Movie Card 背面]
\\\

### 2.2 Navigation Structure

**Primary Navigation**:
- 單頁應用 (SPA)，無傳統導航列
- 狀態切換透過「GENERATE」按鈕觸發

**Secondary Navigation**:
- Header: 標題區域（固定在頂部）
- Main Section: 黑洞 + Mood Orbit + Filters
- Results Section: 推薦結果網格

**Breadcrumb Strategy**:
- 視覺化狀態指示：
  - 選擇階段：黑洞完整顯示
  - 生成中：按鈕變為「生成中...」
  - 結果階段：結果卡片依序進場

### 2.3 Screen Hierarchy

\\\

 1. Header (固定頂部, z-10)                
    - Title: "Movie Recommendation"      
    - Subtitle: "選擇你的心情，發現完美電影"   

 2. Starry Background (fixed, z-0)      
    - 閃爍星星動畫                         
    - 雙層疊加效果                         

 3. Main Interaction Zone (1000px min)  
       
       Black Hole Canvas (800x800)    
       + Mood Orbit (radius=450px)    
       + GENERATE Button (center)     
       

 4. Filter Controls Section             
    - Era Selector (7 chips, max 3)     
    - Genre Selector (19 chips, max 3)  
    - Natural Language Textarea         

 5. Results Grid (conditional, animated)
    - Strategy Info                      
    - 10 Movie Cards (stagger 100ms)    
    - Grid: 1/2/3/4 columns responsive  

\\\

---

## 3. User Flows

### 3.1 Primary Recommendation Flow

**Goal**: 根據當前心情快速找到完美的電影  
**Success Criteria**: 用戶成功獲得 10 部符合心情的電影推薦，完成時間 < 30 秒

**Steps**:
1. 用戶進入頁面  載入黑洞動畫 + Mood Labels
2. Hover Mood Label  顯示 Tooltip（類別 + 描述）
3. Click Mood Label  選中狀態（發光 + 放大 1.1x）
4. 可選：選擇年代/類型篩選（最多各 3 個）
5. 可選：輸入自然語言描述
6. Click GENERATE  驗證是否有選 Mood
7. API 呼叫  生成中狀態（按鈕文字變化 + 黑洞脈衝）
8. 成功  兩段式轉場動畫
   - 黑洞淡化
   - 策略提示淡入
   - Movie Cards 依序進場（stagger 100ms）
9. 用戶可 Hover/Click 卡片查看詳情

### 3.2 Edge Cases

| Case | Behavior | Recovery |
|------|----------|----------|
| 未選 Mood 就 GENERATE | Alert「請至少選擇一個心情標籤」 | 繼續選擇 |
| API 失敗 | Alert「推薦失敗，請稍後再試」 | 可重試 |
| 無推薦結果 | Empty state「找不到符合條件的電影」 | 建議放寬篩選 |
| 超過 Filter 限制 | 其他選項 disabled + 計數器「3/3」 | 取消選擇後可繼續 |
| 圖片載入失敗 | 自動替換 placeholder | onError handler |

---

## 4. Component Library

### 4.1 Core Components

#### BlackHoleCanvas
- **尺寸**: 800x800px
- **星星數量**: 2500
- **動畫**: 60fps 連續旋轉
- **Props**: \onGenerate: () => void\, \isLoading: boolean\
- **技術**: HTML5 Canvas + requestAnimationFrame

#### MoodOrbitButton
- **數量**: 18 個標籤
- **環繞半徑**: 450px
- **States**:
  - Default: \opacity: 0.8\, \g-black/60\
  - Hover: \scale(1.05)\ + Tooltip
  - Selected: \scale(1.1)\ + 發光效果 + 背景填色
- **Tooltip**: 顯示類別 + 描述

#### FilterChip
- **年代**: 7 個選項（60s-20s）
- **類型**: 19 個選項
- **限制**: 最多選 3 個
- **States**:
  - Default: \g-black/50\, \order-gray-700\
  - Hover: \order-purple-500\
  - Selected: \g-purple-500\, shadow
  - Disabled: \opacity-30\, \cursor-not-allowed\

#### MovieFlipCard
- **尺寸**: 高度 450px, 寬度 responsive
- **翻轉**: 700ms Y軸旋轉
- **正面**: 海報 + 標題 + 評分 + 年份
- **背面**: 劇情 + 匹配分數 + CTA (Watch Now, Flip Back)

#### NaturalLanguageInput
- **類型**: Textarea, 3 rows
- **樣式**: \g-black/50\, \order-gray-700\, focus:\order-purple-500\
- **Placeholder**: "例如：我想看一部溫馨感人的家庭電影..."

---

## 5. Branding & Style Guide

### 5.1 Color Palette

| Color Type | Hex Code | Usage |
|------------|----------|-------|
| Primary | \#7C4DFF\ | 按鈕、主要 CTA、選中狀態 |
| Secondary | \#5E35B1\ | Hover 狀態、次要元素 |
| Accent | \#00E5FF\ | 星光、高亮效果 |
| Background | \#000000\ | 主背景（宇宙黑） |
| Success | \#4CAF50\ | 成功提示 |
| Warning | \#FF9800\ | 警告提示 |
| Error | \#F44336\ | 錯誤提示 |
| Neutral Gray | \#gray-700\ | 邊框、分隔線 |

### 5.2 Typography

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| H1 | 48px (3xl) | bold | 1.2 |
| H2 | 32px (2xl) | bold | 1.3 |
| H3 | 20px (xl) | medium | 1.4 |
| Body | 16px (base) | normal | 1.6 |
| Small | 14px (sm) | normal | 1.5 |
| Button | 20px (xl) | bold | 1 |

**Font Families**:
- Primary: System Default (Arial, Helvetica, sans-serif)
- Fallback: Sans-serif

### 5.3 Spacing & Layout

- **Grid System**: Tailwind responsive grid (1/2/3/4 columns)
- **Spacing Scale**: Tailwind default (4px base unit)
- **Max Width**: 1280px (7xl) for content containers

---

## 6. Animation & Micro-interactions

### 6.1 Motion Principles

- **Duration**: 
  - Micro: 200-300ms (hover, focus)
  - Transition: 400-700ms (state changes)
  - Cinematic: 1000-1500ms (page transitions)
- **Easing**: 
  - Default: \ease-out\
  - Bounce: \cubic-bezier(0.68, -0.55, 0.265, 1.55)\
  - Smooth: \cubic-bezier(0.4, 0.0, 0.2, 1)\

### 6.2 Key Animations

| Animation | Target | Duration | Easing | Trigger |
|-----------|--------|----------|--------|---------|
| 黑洞星星旋轉 | Canvas stars | Continuous | linear | On load |
| Mood hover | Mood button | 200ms | ease-out | Hover |
| Mood select | Mood button | 300ms | ease-out | Click |
| Card flip | Movie card | 700ms | ease-in-out | Click |
| Cards enter | Results grid | 400ms | ease-out | API success |
| Twinkle stars | Background | 3-4s | ease-in-out | Continuous |

### 6.3 Stagger Animation

**Results Grid Entry**:
- 每 2 張卡片間隔 100ms
- 從 \	ranslateY(50px), opacity: 0\  \	ranslateY(0), opacity: 1\
- 總時長: ~1.5s (10 cards)

---

## 7. Responsiveness Strategy

### 7.1 Breakpoints

| Breakpoint | Min Width | Max Width | Grid Columns | Black Hole Size |
|------------|-----------|-----------|--------------|-----------------|
| Mobile | 320px | 767px | 1 | 600px (縮小) |
| Tablet | 768px | 1023px | 2 | 700px |
| Desktop | 1024px | 1439px | 3 | 800px |
| Wide | 1440px+ | - | 4 | 800px |

### 7.2 Adaptation Patterns

**Mobile (<768px)**:
- 黑洞縮小為 600x600px
- Mood orbit radius 調整為 350px
- Mood labels 字體縮小
- Filter chips 可滑動
- Movie cards 單列

**Tablet (768-1023px)**:
- 黑洞 700x700px
- Mood orbit radius 400px
- Movie cards 2 列

**Desktop (1024px+)**:
- 黑洞完整 800x800px
- Mood orbit radius 450px
- Movie cards 3-4 列

---

## 8. Accessibility Requirements

### 8.1 Compliance Target

**Standard**: WCAG 2.1 Level AA

### 8.2 Key Requirements

**Visual**:
- Color contrast: 最低 4.5:1 (文字), 3:1 (UI 元件)
- Focus indicators: 2px purple outline
- Text sizing: 支援放大到 200%

**Interaction**:
- Keyboard navigation: Tab 順序邏輯
- Screen reader: ARIA labels 完整
- Touch targets: 最小 44x44px

**Content**:
- Alternative text: 所有圖片有 alt
- Form labels: 每個 input 有 label
- Error messages: 明確且可操作

---

## 9. Performance Considerations

### 9.1 Performance Goals

- **Page Load**: < 2s (LCP)
- **Interaction Response**: < 100ms (FID)
- **Animation FPS**: 60fps (canvas, CSS animations)

### 9.2 Design Strategies

- Canvas 使用 requestAnimationFrame 優化
- 星空背景使用 CSS 而非 canvas
- Movie cards 使用虛擬滾動（如果超過 20 張）
- 圖片使用 WebP 格式 + lazy loading
- 動畫使用 CSS transform (GPU 加速)

---

## 10. Implementation Status

### 10.1 Completed Features 

- [x] BlackHoleCanvas 擴大到 800x800px
- [x] Mood Orbit radius 調整到 450px
- [x] 星空背景動畫（雙層閃爍）
- [x] 自然語言輸入 Textarea
- [x] Movie Cards stagger 進場動畫
- [x] 後端 API 串接（v2 推薦系統）

### 10.2 Backend Integration

**API Endpoint**: \/api/recommend/v2/movies\

**Request Payload**:
\\\json
{
  "query": "string (自然語言)",
  "selected_moods": ["string"],
  "selected_genres": ["string"],
  "selected_eras": ["string"],
  "randomness": 0.3,
  "decision_threshold": 40
}
\\\

**Response**:
\\\json
{
  "movies": [
    {
      "id": "number",
      "title": "string",
      "overview": "string",
      "poster_url": "string | null",
      "release_year": "number | null",
      "vote_average": "number",
      "similarity_score": "number (optional)",
      "feature_score": "number (optional)"
    }
  ],
  "strategy": "Feature | Embedding | Legacy",
  "config": {
    "randomness": 0.3,
    "decision_threshold": 40
  }
}
\\\

---

## 11. Next Steps

### 11.1 Immediate Actions

1. **測試響應式設計** - 在各種裝置上測試黑洞和 Mood Orbit 的顯示
2. **性能優化** - 使用 Lighthouse 測試並優化 LCP/FID
3. **無障礙檢查** - 使用 axe DevTools 檢查 WCAG 合規性
4. **用戶測試** - 進行 5-10 人的可用性測試

### 11.2 Design Handoff Checklist

- [x] 所有使用者流程已文件化
- [x] 元件清單完整
- [x] 無障礙需求已定義
- [x] 響應式策略明確
- [x] 品牌指南已整合
- [x] 性能目標已建立
- [x] 動畫規格已詳細說明
- [x] 後端 API 串接已驗證

---

## 12. Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-09 | 1.0 | 初始版本 - 完整 UI/UX 規格 | UX Expert (Sally) |

---

**文檔結束**
