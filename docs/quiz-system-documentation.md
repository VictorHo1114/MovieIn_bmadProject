# MovieIn 每日電影問答系統文件

## 📋 目錄
1. [系統概述](#系統概述)
2. [系統架構](#系統架構)
3. [資料庫設計](#資料庫設計)
4. [核心功能](#核心功能)
5. [題庫管理](#題庫管理)
6. [自動化流程](#自動化流程)
7. [API 接口](#api-接口)
8. [前端整合](#前端整合)
9. [日常維護](#日常維護)
10. [故障排除](#故障排除)

---

## 系統概述

### 功能簡介
MovieIn 每日電影問答系統是一個互動式遊戲功能，每天為用戶提供 3 道電影相關問答題。用戶答對可獲得積分，系統會自動追蹤答題記錄並避免短期內重複出題。

### 核心特色
- ✅ **每日更新**: 每天凌晨 1:00 自動生成新題目
- ✅ **智能選題**: 避免 10 天內重複出現相同題目
- ✅ **豐富題庫**: 30 道精選電影問答題，涵蓋 6 大類型
- ✅ **積分系統**: 首次答對獲得積分，重答不重複計分
- ✅ **互動體驗**: 翻卡動畫、即時反饋、答題歷史追蹤

### 技術棧
- **後端**: FastAPI + SQLAlchemy + PostgreSQL (Neon)
- **前端**: Next.js 14 + React + TypeScript + Framer Motion
- **自動化**: Windows Task Scheduler + PowerShell

---

## 系統架構

### 數據流程圖
```
┌─────────────────┐
│  QUIZ_TEMPLATES │ (程式碼中的 30 題題庫)
│   30 道題目      │
└────────┬────────┘
         │
         │ 智能選題演算法
         │ (避免 10 天內重複)
         ▼
┌─────────────────────┐
│ generate_daily_quiz.py│ (每日凌晨 1:00 執行)
│   選出 3 道題目       │
└─────────┬───────────┘
          │
          │ 寫入資料庫
          ▼
┌─────────────────┐
│  daily_quiz     │ (PostgreSQL 資料表)
│  儲存當天題目    │
└────────┬────────┘
         │
         │ FastAPI 查詢
         ▼
┌─────────────────┐
│  GET /quiz/today│ (API 接口)
│  回傳 3 道題目   │
└────────┬────────┘
         │
         │ Fetch 請求
         ▼
┌─────────────────────┐
│ HomeQuizWidget.tsx  │ (前端組件)
│  顯示問答卡片       │
└─────────────────────┘
```

### 核心組件關聯
```
backend/
├── tools/generate_daily_quiz.py     ← 【題目生成器】
├── app/models/quiz.py               ← 【資料模型】
├── app/services/quiz_service.py     ← 【業務邏輯】
└── app/api/endpoints/quiz.py        ← 【API 路由】

frontend/
├── components/quiz/HomeQuizWidget.tsx  ← 【主組件】
├── components/quiz/QuestionCard.tsx    ← 【卡片組件】
└── lib/api.ts                          ← 【API 客戶端】

automation/
└── Task Scheduler                      ← 【自動排程】
```

---

## 資料庫設計

### 資料表結構

#### 1. `daily_quiz` - 每日題目表
| 欄位名稱 | 資料型別 | 說明 | 約束 |
|---------|---------|------|------|
| id | Integer | 主鍵 | PRIMARY KEY, AUTO_INCREMENT |
| date | Date | 題目日期 | NOT NULL |
| sequence_number | Integer | 當日題目序號 (1-3) | NOT NULL |
| question | String | 題目文字 | NOT NULL |
| options | JSON | 選項陣列 (4 個選項) | NOT NULL |
| correct_answer | Integer | 正確答案索引 (0-3) | NOT NULL, CHECK |
| explanation | String | 答案解析 | NOT NULL |
| difficulty | String | 難度 (easy/medium/hard) | |
| category | String | 類別 (科幻/劇情/愛情/動作/喜劇/驚悚) | |
| movie_reference | JSON | 電影資訊 (title, year, poster_url) | |

**唯一約束**: `(date, sequence_number)` - 每天的每個序號只能有一道題

**範例資料**:
```json
{
  "id": 1,
  "date": "2025-11-14",
  "sequence_number": 1,
  "question": "《星際效應》中，主角庫珀進入黑洞後看到的五維空間是用來做什麼？",
  "options": ["觀察過去的地球", "與外星人溝通", "傳遞訊息給過去的女兒", "尋找新的星球"],
  "correct_answer": 2,
  "explanation": "在五維空間中，庫珀能夠跨越時間，透過書架向過去的女兒墨菲傳遞重要訊息。",
  "difficulty": "medium",
  "category": "科幻",
  "movie_reference": {
    "title": "星際效應",
    "year": 2014,
    "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg"
  }
}
```

#### 2. `quiz_attempts` - 答題記錄表
| 欄位名稱 | 資料型別 | 說明 |
|---------|---------|------|
| id | Integer | 主鍵 |
| user_id | Integer | 用戶 ID (外鍵 → users.id) |
| quiz_id | Integer | 題目 ID (外鍵 → daily_quiz.id) |
| selected_answer | Integer | 用戶選擇的答案索引 |
| is_correct | Boolean | 是否答對 |
| points_awarded | Integer | 獲得的積分 |
| attempted_at | DateTime | 答題時間 |

**用途**: 追蹤用戶答題歷史，實現「首次答對得分，重答不計分」邏輯

---

## 核心功能

### 1. 智能選題演算法

**目的**: 避免用戶在短期內看到重複題目

**實作邏輯** (`generate_daily_quiz.py`):
```python
def get_recently_used_questions(db, lookback_days=10):
    """取得最近 10 天使用過的題目"""
    cutoff_date = date.today() - timedelta(days=lookback_days)
    
    recent_quizzes = db.query(DailyQuiz).filter(
        DailyQuiz.date >= cutoff_date
    ).all()
    
    # 提取使用過的題目（透過問題文字比對）
    used_questions = {quiz.question for quiz in recent_quizzes}
    return used_questions
```

**選題流程**:
1. 查詢最近 10 天的題目
2. 從 30 題題庫中排除已使用的題目
3. 從剩餘題目中隨機選 3 題
4. 如果可用題目 < 3 題，則從全部題庫選取

**數學保證**:
- 題庫: 30 題
- 每日出題: 3 題
- 完整循環: 30 ÷ 3 = 10 天
- **結論**: 10 天內絕不重複

### 2. 積分機制

**規則** (`quiz_service.py`):
- ✅ **首次答對**: 獲得積分 (easy: 10 分, medium: 15 分, hard: 20 分)
- ❌ **首次答錯**: 不得分
- 🔁 **重答題目**: 不論對錯都不再計分

**實作細節**:
```python
async def submit_answer(db: Session, user_id: int, quiz_id: int, answer: int):
    # 檢查是否已答過此題
    existing_attempt = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == user_id,
        QuizAttempt.quiz_id == quiz_id
    ).first()
    
    is_correct = (answer == quiz.correct_answer)
    
    # 只有首次答對才給分
    if not existing_attempt and is_correct:
        points = {"easy": 10, "medium": 15, "hard": 20}
        points_awarded = points.get(quiz.difficulty, 10)
        # 更新用戶積分...
    else:
        points_awarded = 0
```

### 3. 答題狀態管理

**前端邏輯** (`HomeQuizWidget.tsx`):
```typescript
// 檢測是否為今天首次答題
const isFirstRound = todayAttempts.length === 0;

// 顯示不同模式
{isFirstRound ? (
  <h3>🎮 今日挑戰</h3>
) : (
  <h3>📝 複習模式</h3>
)}
```

**狀態追蹤**:
- `attemptedQuizIds`: 已答過的題目 ID
- `correctAnswers`: 答對的題目記錄
- `isFirstRound`: 是否為首次答題 (影響 UI 顯示)

---

## 題庫管理

### 題庫結構

**位置**: `backend/tools/generate_daily_quiz.py` → `QUIZ_TEMPLATES` 陣列

**總題數**: 30 題

**類別分佈**:
| 類別 | 題數 | 範例電影 |
|-----|------|---------|
| 🚀 科幻 | 8 題 | 星際效應、全面啟動、駭客任務、回到未來、異形、E.T.、銀翼殺手、侏羅紀公園 |
| 🎭 劇情 | 7 題 | 刺激1995、阿甘正傳、當幸福來敲門、美麗人生、辛德勒的名單、綠色奇蹟、教父 |
| 💕 愛情 | 4 題 | 鐵達尼號、手札情緣、真愛每一天、樂來越愛你 |
| 💥 動作 | 5 題 | 黑暗騎士、捍衛戰士、玩命關頭、不可能的任務、終極警探 |
| 😂 喜劇 | 3 題 | 三個傻瓜、摩登大聖、楚門的世界 |
| 😱 驚悚 | 3 題 | 沉默的羔羊、鬥陣俱樂部、記憶拼圖 |

### 題目範本格式

```python
{
    "question": "題目文字",
    "options": ["選項1", "選項2", "選項3", "選項4"],
    "correct_answer": 2,  # 索引 (0-3)
    "explanation": "答案解析",
    "difficulty": "medium",  # easy/medium/hard
    "category": "科幻",
    "movie_reference": {
        "title": "電影名稱",
        "year": 2014,
        "poster_url": "https://image.tmdb.org/t/p/w500/xxx.jpg"
    }
}
```

### 新增題目步驟

1. **編輯檔案**: `backend/tools/generate_daily_quiz.py`
2. **找到 `QUIZ_TEMPLATES` 陣列** (約第 23 行)
3. **在陣列末端新增題目**:
   ```python
   {
       "question": "《你的新電影》中...？",
       "options": ["選項A", "選項B", "選項C", "選項D"],
       "correct_answer": 1,
       "explanation": "解析...",
       "difficulty": "medium",
       "category": "劇情",
       "movie_reference": {
           "title": "你的新電影",
           "year": 2025,
           "poster_url": "海報URL"
       }
   }
   ```
4. **驗證格式**: 確保 JSON 格式正確，正確答案索引在 0-3 範圍內
5. **測試**: 執行 `python tools/generate_daily_quiz.py --date 2025-12-31` 測試新題目

**注意事項**:
- ⚠️ 題目文字不可重複 (智能選題用此判斷)
- ⚠️ 選項數量必須為 4 個
- ⚠️ `correct_answer` 從 0 開始計數

---

## 自動化流程

### Windows Task Scheduler 設定

**任務名稱**: `MovieIn每日電影問答生成`

**執行時間**: 每天凌晨 01:00

**執行命令**:
```
C:\Users\User\Desktop\bmad-method\backend\.venv\Scripts\python.exe
```

**命令參數**:
```
tools\generate_daily_quiz.py
```

**工作目錄**:
```
C:\Users\User\Desktop\bmad-method\backend
```

**任務設定**:
- ✅ 使用電池時允許執行
- ✅ 使用電池時不停止
- ✅ 如果錯過執行時間，盡快啟動

### 管理命令

#### 查看任務狀態
```powershell
Get-ScheduledTask -TaskName "MovieIn每日電影問答生成"
```

#### 手動測試執行
```powershell
Start-ScheduledTask -TaskName "MovieIn每日電影問答生成"
```

#### 查看執行歷史
```powershell
Get-ScheduledTask -TaskName "MovieIn每日電影問答生成" | Get-ScheduledTaskInfo
```

#### 刪除任務
```powershell
Unregister-ScheduledTask -TaskName "MovieIn每日電影問答生成" -Confirm:$false
```

### 重新設定自動化

如果需要重新建立任務，執行:
```powershell
cd C:\Users\User\Desktop\bmad-method\backend
.\setup_auto_quiz.ps1
```

---

## API 接口

### 1. 取得今日題目

**端點**: `GET /api/quiz/today`

**回應格式**:
```json
{
  "quizzes": [
    {
      "id": 1,
      "date": "2025-11-14",
      "sequence_number": 1,
      "question": "《星際效應》中...",
      "options": ["...", "...", "...", "..."],
      "difficulty": "medium",
      "category": "科幻",
      "movie_reference": {
        "title": "星際效應",
        "year": 2014,
        "poster_url": "..."
      }
    }
    // ... 共 3 題
  ]
}
```

**注意**: 不回傳 `correct_answer` 和 `explanation`，避免洩題

### 2. 提交答案

**端點**: `POST /api/quiz/submit`

**請求格式**:
```json
{
  "quiz_id": 1,
  "answer": 2
}
```

**回應格式**:
```json
{
  "is_correct": true,
  "correct_answer": 2,
  "explanation": "在五維空間中...",
  "points_awarded": 15,
  "total_points": 150
}
```

### 3. 取得答題記錄

**端點**: `GET /api/quiz/attempts?date=2025-11-14`

**回應格式**:
```json
{
  "attempts": [
    {
      "quiz_id": 1,
      "selected_answer": 2,
      "is_correct": true,
      "points_awarded": 15,
      "attempted_at": "2025-11-14T10:30:00"
    }
  ]
}
```

---

## 前端整合

### 主組件結構

**檔案**: `frontend/components/quiz/HomeQuizWidget.tsx`

**核心功能**:
1. 從 API 載入今日題目
2. 顯示 3 張問答卡片 (Slider 輪播)
3. 處理用戶答題
4. 即時反饋對錯
5. 更新積分
6. 區分首次答題 vs 複習模式

### 卡片組件

**檔案**: `frontend/components/quiz/QuestionCard.tsx`

**特色**:
- 🎴 **翻卡動畫**: 使用 Framer Motion 實現 3D 翻轉效果
- ✅ **即時反饋**: 答題後顯示綠色 (對) / 紅色 (錯)
- 📊 **答案解析**: 翻轉後顯示正確答案和詳細說明
- 🎬 **電影資訊**: 顯示相關電影海報和年份

### 狀態管理

```typescript
const [quizzes, setQuizzes] = useState<Quiz[]>([]);
const [attemptedQuizIds, setAttemptedQuizIds] = useState<Set<number>>(new Set());
const [correctAnswers, setCorrectAnswers] = useState<Record<number, boolean>>({});
const [isFirstRound, setIsFirstRound] = useState(true);
```

### 積分廣播

答題後使用 `BroadcastChannel` 通知其他組件更新積分:
```typescript
const pointsChannel = new BroadcastChannel('points-update');
pointsChannel.postMessage({ points: data.total_points });
```

---

## 日常維護

### 每日檢查清單

✅ **自動執行** (不需人工介入):
- 每天凌晨 1:00 自動生成題目
- 系統自動選題並寫入資料庫

🔍 **建議檢查** (非必要):
- 每週檢查一次資料庫是否有新題目
- 每月檢查一次 Task Scheduler 執行狀態

### 資料庫檢查工具

**檔案**: `backend/check_quiz2.py`

**用途**: 快速查看資料庫狀態

**執行方式**:
```powershell
cd C:\Users\User\Desktop\bmad-method\backend
.\.venv\Scripts\python.exe check_quiz2.py
```

**輸出範例**:
```
📊 資料庫統計
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
總題目數: 12 題
今日題目數: 3 題

📅 最近的題目日期:
  2025-11-16: 3 題
  2025-11-15: 3 題
  2025-11-14: 3 題
  2025-11-12: 3 題
```

### 手動生成題目

**使用時機**: 需要為特定日期生成題目

**基本用法**:
```powershell
cd backend
.\.venv\Scripts\python.exe tools\generate_daily_quiz.py
```

**指定日期**:
```powershell
python tools\generate_daily_quiz.py --date 2025-12-25
```

**指定題數**:
```powershell
python tools\generate_daily_quiz.py --count 5
```

**關閉智能選題** (允許重複):
```powershell
python tools\generate_daily_quiz.py --no-smart
```

---

## 故障排除

### 問題 1: 首頁沒有顯示今日題目

**可能原因**:
1. 資料庫中沒有今天的題目
2. API 連線失敗
3. 前端未正確載入資料

**排查步驟**:

1️⃣ **檢查資料庫**:
```powershell
cd backend
.\.venv\Scripts\python.exe check_quiz2.py
```
確認「今日題目數」是否為 3 題

2️⃣ **手動生成題目**:
```powershell
cd backend
.\.venv\Scripts\python.exe tools\generate_daily_quiz.py
```

3️⃣ **檢查 API**:
在瀏覽器開啟: `http://localhost:8000/api/quiz/today`
應看到 3 題的 JSON 資料

4️⃣ **檢查前端 Console**:
按 F12 查看是否有錯誤訊息

---

### 問題 2: 自動化任務未執行

**檢查任務狀態**:
```powershell
Get-ScheduledTask -TaskName "MovieIn每日電影問答生成" | Select-Object TaskName, State, LastRunTime, NextRunTime
```

**預期輸出**:
```
TaskName                  : MovieIn每日電影問答生成
State                     : Ready
LastRunTime               : 11/14/2025 1:00:00 AM
NextRunTime               : 11/15/2025 1:00:00 AM
```

**如果 State 不是 Ready**:
```powershell
# 刪除並重建任務
Unregister-ScheduledTask -TaskName "MovieIn每日電影問答生成" -Confirm:$false
cd C:\Users\User\Desktop\bmad-method\backend
.\setup_auto_quiz.ps1
```

**查看執行歷史**:
```powershell
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" | 
  Where-Object { $_.Message -like "*MovieIn*" } | 
  Select-Object TimeCreated, Message -First 5
```

---

### 問題 3: 題目重複出現

**可能原因**:
- 智能選題未正常運作
- 題庫不足 (少於 10 天用量)

**解決方案**:

1️⃣ **檢查題庫數量**:
```powershell
cd backend
.\.venv\Scripts\python.exe -c "from tools.generate_daily_quiz import QUIZ_TEMPLATES; print(f'題庫共有 {len(QUIZ_TEMPLATES)} 題')"
```
應顯示: `題庫共有 30 題`

2️⃣ **驗證智能選題**:
執行生成時會顯示可用題目數:
```
✓ 智能選題: 從 27 個未使用的題目中選擇（排除最近 10 天）
```

3️⃣ **暫時關閉智能選題** (測試用):
```powershell
python tools\generate_daily_quiz.py --no-smart
```

---

### 問題 4: 積分未正確計算

**檢查流程**:

1️⃣ **確認答題記錄**:
查詢資料庫 `quiz_attempts` 表，確認 `points_awarded` 欄位

2️⃣ **驗證邏輯**:
- 首次答對: 應有積分 (10/15/20)
- 重答: `points_awarded` 應為 0

3️⃣ **測試 API**:
```bash
curl -X POST http://localhost:8000/api/quiz/submit \
  -H "Content-Type: application/json" \
  -d '{"quiz_id": 1, "answer": 2}'
```

---

## 系統擴展建議

### 短期優化
- [ ] 增加題庫至 60 題 (延長循環週期至 20 天)
- [ ] 新增題目難度篩選功能
- [ ] 支援用戶答題統計圖表

### 長期規劃
- [ ] 多語系支援 (英文、日文題目)
- [ ] 用戶自訂題庫功能
- [ ] 排行榜系統
- [ ] 題目評論與評分

---

## 聯絡與支援

**開發團隊**: MovieIn Team  
**專案位置**: `C:\Users\User\Desktop\bmad-method`  
**文件版本**: v1.0 (2025-11-14)

**相關文件**:
- [後端 API 文件](../backend/README.md)
- [前端開發指南](../frontend/README.md)
- [資料庫架構](../docs/core-architecture.md)

---

*本文件涵蓋了每日電影問答系統的完整技術細節，包括架構設計、資料流程、API 接口、自動化設定、日常維護和故障排除。如有任何問題，請參考相關章節或聯繫開發團隊。*
