# 遊戲問答系統維護指南

## 問題診斷

如果首頁遊戲區沒有新的遊戲卡出現，原因是**資料庫中沒有當天的問題**。

## 解決方案

### 方法 1: 使用自動生成腳本（推薦）

在 `backend/tools/` 目錄下，我們提供了自動生成每日問題的腳本。

#### 為今天生成問題：
```bash
cd backend
.\.venv\Scripts\python.exe tools\generate_daily_quiz.py
```

#### 為特定日期生成問題：
```bash
.\.venv\Scripts\python.exe tools\generate_daily_quiz.py --date 2025-11-15
```

#### 自訂問題數量：
```bash
.\.venv\Scripts\python.exe tools\generate_daily_quiz.py --count 5
```

### 方法 2: 手動在資料庫新增

使用 SQL 直接插入問題（參考 `backend/tools/example_quiz_with_poster.sql`）：

```sql
INSERT INTO daily_quiz (
    date, 
    sequence_number, 
    question, 
    options, 
    correct_answer, 
    explanation, 
    difficulty, 
    category, 
    movie_reference
) VALUES (
    ''2025-11-14'',
    1,
    ''《星際效應》中，主角庫珀進入黑洞後看到的五維空間是用來做什麼？'',
    ''["觀察過去的地球", "與外星人溝通", "傳遞訊息給過去的女兒", "尋找新的星球"]''::jsonb,
    2,
    ''在五維空間中，庫珀能夠跨越時間，透過書架向過去的女兒墨菲傳遞重要訊息。'',
    ''medium'',
    ''科幻'',
    ''{
        "title": "星際效應",
        "year": 2014,
        "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg"
    }''::jsonb
);
```

## 檢查問題狀態

使用檢查腳本查看資料庫中的問題：

```bash
cd backend
.\.venv\Scripts\python.exe check_quiz2.py
```

輸出範例：
```
=== Database Quiz Status ===
Total quizzes: 6
Today (2025-11-14): 3 quizzes
Yesterday (2025-11-13): 0 quizzes

OK: Found 3 quizzes for today

Recent dates with quizzes:
  2025-11-14: 3 quizzes
  2025-11-12: 3 quizzes
```

## 自動化建議

### 選項 1: Windows 工作排程器

1. 開啟「工作排程器」
2. 建立基本工作
3. 設定每日凌晨執行
4. 動作：執行程式
   - 程式：`C:\Users\User\Desktop\bmad-method\backend\.venv\Scripts\python.exe`
   - 引數：`tools\generate_daily_quiz.py`
   - 起始於：`C:\Users\User\Desktop\bmad-method\backend`

### 選項 2: 使用 Cron（Linux/Mac）

```bash
# 每天凌晨 1 點自動生成
0 1 * * * cd /path/to/backend && .venv/bin/python tools/generate_daily_quiz.py
```

## 擴充問題庫

編輯 `backend/tools/generate_daily_quiz.py` 中的 `QUIZ_TEMPLATES` 陣列，新增更多問題：

```python
QUIZ_TEMPLATES = [
    {
        "question": "你的問題？",
        "options": ["選項1", "選項2", "選項3", "選項4"],
        "correct_answer": 0,  # 0-3
        "explanation": "答案解釋",
        "difficulty": "easy",  # easy, medium, hard
        "category": "科幻",
        "movie_reference": {
            "title": "電影名稱",
            "year": 2024,
            "poster_url": "https://image.tmdb.org/t/p/w500/xxx.jpg"
        }
    },
    # ... 更多問題
]
```

## 系統架構

### 資料表結構

- `daily_quiz`: 每日問題表
  - `date`: 問題日期（每天可有多題）
  - `sequence_number`: 該日的題號（1, 2, 3）
  - `question`: 問題內容
  - `options`: 4個選項（JSONB）
  - `correct_answer`: 正確答案索引（0-3）
  - `explanation`: 答案說明
  - `movie_reference`: 電影參考資訊（JSONB）

- `quiz_attempts`: 使用者答題記錄
  - 記錄使用者的答題歷史
  - 支援重玩模式（不計分）

### 前端元件

- `HomeQuizWidget.tsx`: 首頁問答小工具
- `QuestionCard.tsx`: 翻牌式問題卡片

### 後端 API

- `GET /api/v1/quiz/today`: 取得今天的單一問題（首次答題）
- `GET /api/v1/quiz/today/all`: 取得今天的所有問題（重玩模式）
- `POST /api/v1/quiz/submit`: 提交答案

## 疑難排解

### 問題：前端顯示「沒有問題」

**原因**: 資料庫中沒有今天的問題

**解決**: 執行 `generate_daily_quiz.py` 為今天生成問題

### 問題：生成腳本失敗

**檢查**:
1. 確認虛擬環境已啟用
2. 確認 DATABASE_URL 設定正確
3. 檢查資料庫連線

### 問題：重複的問題

**說明**: 腳本會先檢查是否已有該日期的問題，並詢問是否覆蓋

## 未來改進建議

1. **整合 OpenAI API**: 自動生成電影相關問題
2. **從 TMDB 抓取**: 根據熱門電影自動生成問題
3. **難度調整**: 根據使用者答題歷史調整難度
4. **分類擴充**: 新增更多電影類型分類
5. **多語言支援**: 支援英文等其他語言

---

## 快速參考

```bash
# 檢查今天是否有問題
python check_quiz2.py

# 為今天生成問題
python tools/generate_daily_quiz.py

# 為明天生成問題
python tools/generate_daily_quiz.py --date 2025-11-15

# 生成5題
python tools/generate_daily_quiz.py --count 5
```
