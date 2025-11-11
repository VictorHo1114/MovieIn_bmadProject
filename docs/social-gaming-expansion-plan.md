# MovieIN 社交與遊戲化擴展規劃

**文檔版本：** v1.0  
**建立日期：** 2025-11-12  
**負責人：** Mary (Business Analyst)  
**專案狀態：** 規劃階段

---

## 🎯 核心願景

> 將 MovieIN 從「個人化電影推薦工具」進化為「以電影為連結的社交娛樂平台」，透過遊戲化機制增加用戶黏著度與互動頻率。

**核心價值主張：**
- 🎬 AI 驅動的個人化推薦（現有優勢）
- 👥 輕量級社交互動（品味相似的影迷連結）
- 🎮 遊戲化元素（每日挑戰增加黏著度）
- 📊 數據可視化（觀影統計與比較）

---

## 📊 功能架構總覽

```
MovieIN 2.0
├── 🎬 核心功能（現有）
│   ├── AI 推薦系統（BlackHole 互動）
│   ├── 個人 Top 10 清單
│   ├── Watchlist 待看清單
│   └── 電影搜尋與瀏覽
│
├── 👥 社交功能（新增）
│   ├── 好友系統
│   ├── Profile 擴充
│   ├── 動態牆
│   ├── 片單比較
│   └── 社交互動（點讚、留言）
│
├── 🎮 遊戲化功能（新增）
│   ├── 每日電影問答
│   ├── 積分系統
│   ├── 等級與排行榜
│   └── 成就徽章
│
└── 📊 數據分析（新增）  (不用做)
    ├── 觀影統計 
    ├── 類型偏好分析
    └── 好友相似度比較
```

---

## 階段一：社交基礎建設（MVP）

### 1. 好友系統 👥

#### 1.1 好友管理核心功能

**搜尋與邀請：**
- 依使用者名稱搜尋
- 依使用者 ID 搜尋
- 發送好友邀請
- 接受/拒絕邀請通知

**好友列表：**
- 顯示所有好友
- 線上狀態指示器（綠點）
- 最後活動時間
- 快速操作選單（查看 Profile、移除好友）

**隱私與安全：**
- 封鎖使用者功能
- 移除好友功能
- 好友請求管理（待處理、已拒絕）

#### 1.2 隱私設定選項 (先採全公開，交友軟體的感覺)

**Profile 可見性：**
- 🌐 公開（所有人可見）
- 👥 僅好友（預設）
- 🔒 私密（僅自己）

**清單可見性：**
- Top 10 清單：公開/好友/私密
- Watchlist：公開/好友/私密
- 觀影歷史：公開/好友/私密
- 活動動態：公開/好友/關閉

#### 1.3 好友發現機制 (先不用做)

**推薦演算法：**
1. **共同好友推薦**
   - 「你可能認識：有 3 位共同好友」
   
2. **品味相似推薦**
   - 基於 Top 10 片單重疊度
   - 「這位使用者與你有 60% 相似品味」
   
3. **地理位置推薦**（可選功能）
   - 「附近的影迷」
   - 需使用者授權位置權限

---

### 2. Profile 頁面擴充 🎭

#### 2.1 個人資訊區塊

**現有欄位：**
- 頭像
- 顯示名稱

**新增欄位：**
- 📝 個人簡介（最多 200 字）
- 🎬 最愛電影類型（最多 5 個標籤）
- ⏰ 觀影習慣標籤（例如：深夜觀影黨、週末電影院）
- 📅 加入日期
- 🏆 會員等級徽章
- 📊 總積分 & 排行榜排名

#### 2.2 Profile 個人資料區的更新

```
┌─────────────────────────────────────────┐
│ 👤 頭像           Victor的電影宇宙      │
│                  📊 積分：2,450          │
│                  🏆 等級：影評達人 LV.5  │
│                  📈 排名：#127           │
├─────────────────────────────────────────┤
│ 📝 個人簡介                             │
│ 熱愛科幻與懸疑片，最喜歡諾蘭的作品...   │
│                                         │
│ 🎬 最愛類型：科幻 / 驚悚 / 動作         │
│ ⏰ 觀影習慣：深夜觀影黨 🦉              │
│ 📅 加入時間：2025-06-15                │
├─────────────────────────────────────────┤
│ 🏅 成就徽章 (8個) - NEW                │
│ 🔥 七日連勝  🎯 百發百中  👥 社交達人   │
│ [徽章圖示展示區]                        │
├─────────────────────────────────────────┤
│ 👥 社交數據 - NEW                       │
│ • 好友數量：23 位                         │
└─────────────────────────────────────────┘
編輯個人資料(換名字，顯示郵件) -> 以有功能

└─────────────────────────────────────────┘
```

#### 2.3 新增數據統計模組 (不用做)

**觀影統計儀表板：**
- 總觀影數 / 本月觀影數
- 類型分佈圖（圓餅圖）
  - 科幻：30%
  - 劇情：25%
  - 動作：20%
  - 其他：25%
- 年代偏好圖（長條圖）
  - 2020s: ████████ 32部
  - 2010s: ██████ 24部
  - 2000s: ████ 16部
- 平均評分趨勢線圖

**社交互動數據：**
- 好友總數
- 本月新增好友
- 獲得的點讚數
- 發布的動態數

---

## 階段二：遊戲化系統 🎮

### 3. 每日電影問答

#### 3.1 遊戲機制設計

**核心規則：**
- ⏰ 每日更新 1 題（凌晨 00:00 UTC+8 刷新）
- 🎯 4 選 1 選擇題
- ⏱️ 每題限時 30 秒
- ✅ 答對：+10 分
- ❌ 答錯：+0 分（不扣分策略，降低挫折感）
- 🚫 每題只能答 1 次
- 📅 錯過當日題目即無法補答

**連勝獎勵機制：**(不用做)
- 連續 3 天答對：+5 額外積分
- 連續 7 天答對：+50 額外積分 + 🔥 徽章
- 連續 30 天答對：+200 額外積分 + 👑 傳奇徽章

#### 3.2 題目類型分類

**1. 電影知識類（40%）**

範例題目：
```
Q: 哪位演員沒有出演過《復仇者聯盟》系列？
A. 小勞勃道尼
B. 克里斯伊凡
C. 湯姆克魯斯 ✓ (正確答案)
D. 史嘉蕾喬韓森
```

子類別：
- 演員陣容識別
- 導演作品配對
- 得獎紀錄查詢
- 電影系列排序

**2. 劇情細節類（30%）**

範例題目：
```
Q: 經典台詞 "May the Force be with you" 出自哪部電影？
A. 星際大戰 ✓
B. 星際爭霸戰
C. 星際效應
D. 星際異攻隊
```

子類別：
- 經典台詞來源
- 情節轉折辨識
- 角色關係謎題
- 彩蛋線索追蹤

**3. 幕後花絮類（20%）**

範例題目：
```
Q: 《魔戒》三部曲的主要拍攝地點在哪個國家？
A. 英國
B. 紐西蘭 ✓
C. 澳洲
D. 冰島
```

子類別：
- 拍攝地點
- 特效技術
- 製作預算
- 幕後故事

**4. 視覺識別類（10%）**

範例題目：
```
Q: 以下是哪部電影的經典場景？
[顯示電影截圖]
A. 全面啟動 ✓
B. 駭客任務
C. 記憶拼圖
D. 羅根
```

子類別：
- 海報局部辨識
- 場景截圖猜片
- 角色剪影識別
- 配樂片段辨識（進階功能）

#### 3.3 答題介面設計

**首頁入口卡片：**
```
┌────────────────────────────────┐
│ 🎯 今日電影挑戰                │
│ ⏰ 12:34:56 後刷新              │
│                                │
│ 🔴 [未完成] → 點擊進入答題     │
│                                │
│ 📊 本週戰績                    │
│ • 答對：5/6 題                 │
│ • 正確率：83%                  │
│ • 🔥 連續答對：5 天            │
│                                │
│ 🏆 本月總分：120 分            │
└────────────────────────────────┘
```

**答題頁面：**
```
┌────────────────────────────────┐
│ 🎬 每日電影知識 - 2025/11/12   │
│ ⏱️ 剩餘時間：00:27             │
│                                │
│ 類型：電影知識 | 難度：⭐⭐    │
│                                │
│ Q: 哪位演員沒演過《復仇者聯盟》？│
│                                │
│ ┌─────────────────────┐        │
│ │ A. 小勞勃道尼        │        │
│ └─────────────────────┘        │
│ ┌─────────────────────┐        │
│ │ B. 克里斯伊凡        │        │
│ └─────────────────────┘        │
│ ┌─────────────────────┐        │
│ │ C. 湯姆克魯斯  ✓     │ ← 已選 │
│ └─────────────────────┘        │
│ ┌─────────────────────┐        │
│ │ D. 史嘉蕾喬韓森      │        │
│ └─────────────────────┘        │
│                                │
│       [確認答案]               │
└────────────────────────────────┘
```

**結果頁面：**
```
┌────────────────────────────────┐
│ ✅ 恭喜答對！                  │
│                                │
│ 🎉 +10 分                      │
│ 🔥 連續答對 6 天               │
│                                │
│ 💡 小知識                      │
│ 湯姆克魯斯主演的是《不可能的任務》│
│ 系列，並非漫威宇宙的一員。     │
│                                │
│ 📊 今日全站正確率：67%         │
│                                │
│ [分享戰績] [查看排行榜]        │
└────────────────────────────────┘
```

---

### 4. 積分與成就系統

#### 4.1 積分獲取途徑

| 行為 | 積分 | 每日上限 | 說明 |
|------|------|---------|------|
| 每日問答答對 | +10 | 10 | 基礎積分 |
| 連續 3 天答對 | +5 | - | 連勝獎勵 |
| 連續 7 天答對 | +50 | - | 週連勝 |
| 連續 30 天答對 | +200 | - | 月連勝 |
| 新增電影至 Top 10 | +5 | 25 | 最多 5 次/日 |
| 完成觀影打卡 | +3 | 30 | 最多 10 次/日 |
| 獲得好友點讚 | +2 | 20 | 最多 10 次/日 |
| 新增好友 | +5 | 25 | 最多 5 次/日 |
| 撰寫影評（未來） | +15 | 45 | 最多 3 次/日 |
| 獲得影評點讚（未來） | +3 | 30 | 最多 10 次/日 |

**每日積分上限設計理念：**
- 防止刷分行為
- 鼓勵多元化互動
- 保持長期平衡性

#### 4.2 會員等級系統

```
🎬 LV.1 電影新手    (0-99 分)
   • 解鎖：基礎功能
   • 特權：無

🎞️ LV.2 影迷見習    (100-299 分)
   • 解鎖：自訂 Profile 主題色
   • 特權：每日問答提示 1 次

🎭 LV.3 觀影達人    (300-599 分)
   • 解鎖：進階統計圖表
   • 特權：好友上限提升至 100 人

🏆 LV.4 影評專家    (600-999 分)
   • 解鎖：專屬徽章邊框
   • 特權：可建立影迷小組（未來）

👑 LV.5 電影宗師    (1000+ 分)
   • 解鎖：全站唯一稱號
   • 特權：排行榜永久顯示
```

#### 4.3 成就徽章系統 (不用做)

**基礎成就：**
- 🎬 **新手上路**：完成 Profile 設定
- 📝 **自我介紹**：撰寫個人簡介
- 🔟 **十全十美**：完成 Top 10 清單
- 📚 **書蟲養成**：Watchlist 達到 20 部

**社交成就：**
- 👥 **社交新星**：擁有 5 位好友
- 🌟 **社交達人**：擁有 20 位好友
- 💬 **互動王**：獲得 50 個讚
- 🔥 **人氣爆棚**：單則動態獲得 20 讚

**挑戰成就：**
- 🎯 **初試啼聲**：答對第 1 題
- 🔥 **七日連勝**：連續 7 天答對
- 💯 **百發百中**：累計答對 100 題
- 🏆 **完美月份**：單月全勤且全對

**觀影成就：**
- 🎞️ **觀影入門**：記錄 10 部電影
- 📊 **觀影達人**：記錄 50 部電影
- 👑 **觀影大師**：記錄 100 部電影
- 🌈 **類型探索家**：觀看 10 種不同類型

**特殊成就：**
- 🌙 **深夜影迷**：凌晨 2-5 點答題 10 次
- ⚡ **閃電俠**：5 秒內答對 10 題
- 🎁 **早鳥優惠**：在題目發布 1 小時內答題 30 次

---

## 階段三：社交互動強化 不用做

### 5. 動態牆功能 📱 (不用做)

#### 5.1 個人動態類型

**自動發布動態：**
1. **Top 10 更新**
   ```
   Victor 將《星際效應》加入 Top 10 第 3 名
   ⏰ 2 小時前
   💬 2 則留言  ❤️ 5
   ```

2. **每日挑戰完成**
   ```
   Victor 完成今日電影挑戰！答對了！🎉
   連續答對 3 天 🔥
   ⏰ 5 小時前
   💬 留言  ❤️ 3
   ```

3. **成就解鎖**
   ```
   Victor 解鎖成就：🏆 七日連勝
   ⏰ 1 天前
   💬 5 則留言  ❤️ 12
   ```

4. **觀影打卡**
   ```
   Victor 剛看完《全面啟動》
   評分：⭐⭐⭐⭐⭐ 5.0
   「諾蘭的神作，每次重看都有新發現！」
   ⏰ 3 小時前
   💬 8 則留言  ❤️ 15
   ```

#### 5.2 好友動態牆

**動態牆介面：**
```
┌──────────────────────────────┐
│ 📢 好友動態                   │
│ [全部 | 好友 | 僅我的]        │
├──────────────────────────────┤
│ 👤 Alice Lin                 │
│ 更新了 Top 10 清單            │
│ 將《駭客任務》加入第 1 名     │
│                              │
│ 💬 2 則留言  ❤️ 5            │
│ ⏰ 2 小時前                   │
├──────────────────────────────┤
│ 👤 Bob Chen                  │
│ 完成今日電影挑戰！            │
│ 答對了！連續 5 天 🔥          │
│                              │
│ 💬 留言  ❤️ 3                │
│ ⏰ 5 小時前                   │
├──────────────────────────────┤
│ 👤 Carol Wang                │
│ 解鎖成就：🎯 百發百中         │
│                              │
│ 💬 5 則留言  ❤️ 12           │
│ ⏰ 1 天前                     │
└──────────────────────────────┘
```

#### 5.3 互動功能

**基礎互動：**
- 👍 點讚動態（可取消）
- 💬 留言回覆（巢狀回覆，最多 2 層）
- 🔗 分享至外部（Twitter、Facebook）
- 🔖 收藏動態（個人書籤）

**通知系統：**
- 🔔 有人對你的動態按讚
- 💬 有人回覆你的留言
- 👥 有人接受你的好友邀請
- 🏆 你獲得新徽章
- 🎯 每日問答已刷新

---

### 6. 片單比較功能 🔍

#### 6.1 好友片單比較

**比較介面：**
```
┌──────────────────────────────┐
│ 🎬 與 Alice 的片單比較        │
│ 品味相似度：72% 💚            │
├──────────────────────────────┤
│ 💚 共同喜愛 (3部)             │
│ • ⭐ 星際效應                 │
│ • ⭐ 全面啟動                 │
│ • ⭐ 黑暗騎士                 │
│                              │
│ [一起討論這些電影]            │
├──────────────────────────────┤
│ 🔵 你喜歡，Alice 沒看過 (5部) │
│ • 記憶拼圖                    │
│ • 敦克爾克大行動              │
│ • 星際效應                    │
│ • 頂尖對決                    │
│ • 黑暗騎士：黎明升起          │
│                              │
│ [推薦給 Alice]                │
├──────────────────────────────┤
│ 🟣 Alice 喜歡，你沒看過 (4部) │
│ • 銀翼殺手 2049               │
│ • 沙丘                        │
│ • 駭客任務                    │
│ • 異星入境                    │
│                              │
│ [加入我的待看清單]            │
└──────────────────────────────┘
```

#### 6.2 相似度計算演算法

**計算公式：**
```
相似度 = (共同電影數 × 2) / (用戶A電影數 + 用戶B電影數) × 100%

範例：
- 共同電影：3 部
- Alice Top 10：10 部
- Victor Top 10：10 部
- 相似度 = (3 × 2) / (10 + 10) × 100% = 30%
```

**相似度等級：**
- 🔥 90-100%：靈魂伴侶
- 💚 70-89%：品味相近
- 💙 50-69%：略有重疊
- 💛 30-49%：有些共鳴
- 🤍 0-29%：品味迥異

---

## 🗄️ 資料庫設計

### 新增資料表結構

#### 1. 好友關係表 (friendships)
```sql
CREATE TABLE friendships (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    friend_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, accepted, rejected, blocked
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, friend_id)
);

CREATE INDEX idx_friendships_user_id ON friendships(user_id);
CREATE INDEX idx_friendships_friend_id ON friendships(friend_id);
CREATE INDEX idx_friendships_status ON friendships(status);
```

#### 2. 積分歷史表 (points_history)
```sql
CREATE TABLE points_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL, -- quiz_correct, watchlist_add, review_post, etc.
    points INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_points_user_id ON points_history(user_id);
CREATE INDEX idx_points_created_at ON points_history(created_at);
```

#### 3. 每日問答表 (daily_quiz)
```sql
CREATE TABLE daily_quiz (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer CHAR(1) NOT NULL, -- 'A', 'B', 'C', 'D'
    category VARCHAR(50) NOT NULL, -- knowledge, plot, behind_scenes, visual
    difficulty INTEGER DEFAULT 1, -- 1-5
    explanation TEXT,
    quiz_date DATE NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_quiz_date ON daily_quiz(quiz_date);
CREATE INDEX idx_quiz_category ON daily_quiz(category);
```

#### 4. 答題記錄表 (quiz_attempts)
```sql
CREATE TABLE quiz_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_id INTEGER NOT NULL REFERENCES daily_quiz(id) ON DELETE CASCADE,
    selected_answer CHAR(1) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    time_taken INTEGER, -- seconds
    answered_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, quiz_id)
);

CREATE INDEX idx_attempts_user_id ON quiz_attempts(user_id);
CREATE INDEX idx_attempts_quiz_id ON quiz_attempts(quiz_id);
CREATE INDEX idx_attempts_answered_at ON quiz_attempts(answered_at);
```

#### 5. 徽章定義表 (badges)
```sql
CREATE TABLE badges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50), -- emoji or icon name
    category VARCHAR(50), -- social, challenge, viewing, special
    requirement_type VARCHAR(50), -- streak_days, total_count, etc.
    requirement_value INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 6. 使用者徽章表 (user_badges)
```sql
CREATE TABLE user_badges (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, badge_id)
);

CREATE INDEX idx_user_badges_user_id ON user_badges(user_id);
```

#### 7. 動態表 (activities)
```sql
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- top10_update, quiz_complete, badge_earned, movie_watch
    content JSONB, -- flexible content storage
    visibility VARCHAR(20) DEFAULT 'friends', -- public, friends, private
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_activities_user_id ON activities(user_id);
CREATE INDEX idx_activities_type ON activities(activity_type);
CREATE INDEX idx_activities_created_at ON activities(created_at DESC);
```

#### 8. 互動表 (interactions)
```sql
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    activity_id INTEGER NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    interaction_type VARCHAR(20) NOT NULL, -- like, comment
    content TEXT, -- for comments
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(activity_id, user_id, interaction_type) WHERE interaction_type = 'like'
);

CREATE INDEX idx_interactions_activity_id ON interactions(activity_id);
CREATE INDEX idx_interactions_user_id ON interactions(user_id);
```

#### 9. 觀影歷史表 (viewing_history)
```sql
CREATE TABLE viewing_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tmdb_id INTEGER NOT NULL,
    rating DECIMAL(2,1), -- 1.0-5.0
    review TEXT,
    watched_at DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, tmdb_id, watched_at)
);

CREATE INDEX idx_viewing_user_id ON viewing_history(user_id);
CREATE INDEX idx_viewing_watched_at ON viewing_history(watched_at DESC);
```

#### 10. 擴充 users 表欄位
```sql
ALTER TABLE users ADD COLUMN bio TEXT;
ALTER TABLE users ADD COLUMN favorite_genres JSONB DEFAULT '[]'::jsonb;
ALTER TABLE users ADD COLUMN viewing_habits JSONB DEFAULT '[]'::jsonb;
ALTER TABLE users ADD COLUMN total_points INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN profile_visibility VARCHAR(20) DEFAULT 'friends';
ALTER TABLE users ADD COLUMN joined_at TIMESTAMP DEFAULT NOW();
```

---

## 📅 實作時程規劃

### Phase 1: 社交基礎（2-3 週）

**Week 1-2: 好友系統**
- [ ] 資料庫 Schema 設計與建立
- [ ] 好友 CRUD API（發送邀請、接受、拒絕、移除）
- [ ] 好友列表 UI
- [ ] 搜尋使用者功能
- [ ] 隱私設定 API 與 UI

**Week 3: Profile 擴充**
- [ ] 擴充 users 表欄位
- [ ] Profile 編輯 API
- [ ] Profile 展示頁 UI 改版
- [ ] 觀影統計基礎功能
- [ ] 成就徽章顯示區

---

### Phase 2: 遊戲化核心（1-2 週）

**Week 4: 每日問答系統**
- [ ] daily_quiz 與 quiz_attempts 表建立
- [ ] 每日問答 CRUD API
- [ ] 答題頁面 UI
- [ ] 結果頁面 UI
- [ ] 積分計算邏輯
- [ ] 首批 30 題題庫建立

**Week 5: 積分與排行榜**
- [ ] points_history 表與 API
- [ ] 積分統計查詢 API
- [ ] 等級計算邏輯
- [ ] 排行榜 API（全站、好友）
- [ ] 排行榜 UI
- [ ] 徽章系統基礎架構

---

### Phase 3: 社交互動（2 週）

**Week 6: 動態牆基礎**
- [ ] activities 表建立
- [ ] 自動發布動態邏輯（Top 10 更新、問答完成）
- [ ] 動態牆 API（取得好友動態）
- [ ] 動態牆 UI（顯示列表）
- [ ] 點讚功能 API 與 UI

**Week 7: 互動功能**
- [ ] interactions 表建立
- [ ] 留言功能 API
- [ ] 留言 UI（巢狀回覆）
- [ ] 通知系統基礎架構
- [ ] 好友發現推薦演算法

---

### Phase 4: 深度功能（未來規劃）

**Future Enhancements:**
- 私訊系統
- 影評撰寫與評論
- 影迷小組/社群
- 挑戰賽（週賽、月賽）
- 配樂辨識題型
- 地理位置社交
- 成就分享至社群媒體

---

## 🎯 成功指標（KPI）

### 用戶參與度
- **DAU/MAU 比率**：目標 > 30%
- **每日問答參與率**：目標 > 50%
- **好友平均數**：目標 > 10 位/用戶
- **動態發布頻率**：目標 > 2 則/週/用戶

### 留存率
- **次日留存**：目標 > 40%
- **七日留存**：目標 > 25%
- **三十日留存**：目標 > 15%

### 社交互動
- **好友邀請接受率**：目標 > 60%
- **動態互動率**（點讚+留言）：目標 > 20%
- **片單分享率**：目標 > 10%

### 遊戲化效果
- **連續答題天數中位數**：目標 > 7 天
- **徽章解鎖平均數**：目標 > 5 個/用戶
- **積分分佈**：前 20% 用戶積分 > 500

---

## 🏆 競品分析

### Letterboxd
**優勢：**
- 成熟的影評社群
- 精美的 UI 設計
- 強大的電影資料庫整合

**劣勢：**
- 缺乏遊戲化元素
- 無 AI 推薦功能
- 英文為主，中文支援不足

### 豆瓣電影
**優勢：**
- 龐大的中文使用者基礎
- 豐富的討論內容
- 完整的評分系統

**劣勢：**
- 介面老舊
- 無遊戲化機制
- 推薦演算法較簡單

### MovieIN 的差異化優勢
✨ **AI 驅動推薦**：BlackHole 互動式推薦體驗  
🎮 **遊戲化設計**：每日問答 + 積分系統  
🎯 **輕量級社交**：專注片單分享，避免過度論壇化  
📊 **視覺化數據**：觀影統計與好友比較  
🌏 **繁體中文優先**：針對台灣市場優化

---

## 💡 實作建議與注意事項

### 技術建議

**前端：**
- 使用 React Query 管理社交互動的快取
- 動態牆採用虛擬滾動（react-window）優化效能
- 積分動畫使用 Framer Motion
- 考慮使用 WebSocket 實現即時通知

**後端：**
- 積分計算採用事務（Transaction）確保一致性
- 排行榜使用 Redis 快取
- 每日問答使用 Cron Job 定時發布
- 好友推薦演算法可考慮背景任務處理

**資料庫：**
- 對高頻查詢欄位建立索引
- 考慮對動態牆資料做分表（按時間）
- 積分歷史可考慮歸檔舊資料

### 使用者體驗建議

**遊戲化平衡：**
- 避免過度獎勵導致通膨
- 設定每日積分上限防止刷分
- 連勝機制要容錯（允許 1 次失誤）

**社交隱私：**
- 預設隱私設定為「僅好友」
- 提供一鍵「全部公開/全部私密」快捷鍵
- 封鎖功能要完全隔離

**內容審核：**
- 簡介與留言需過濾敏感詞
- 考慮使用者檢舉機制
- 建立社群守則（Community Guidelines）

### 營運建議

**題庫管理：**
- 初期手動建立高品質題目（100 題起）
- 中期考慮眾包（用戶提交題目）
- 長期可用 GPT API 輔助生成

**冷啟動策略：**
- 邀請制 Beta 測試（邀請碼）
- 舉辦「首發用戶專屬徽章」活動
- 與電影社群合作推廣

**持續優化：**
- A/B 測試不同積分獎勵設定
- 收集使用者回饋調整難度
- 追蹤熱門電影更新題目

---

## 📝 附錄：功能優先順序矩陣

| 功能 | 重要性 | 緊急性 | 實作難度 | 優先級 |
|------|--------|--------|----------|--------|
| 好友系統 CRUD | 高 | 高 | 中 | P0 |
| Profile 擴充 | 高 | 高 | 低 | P0 |
| 每日問答核心 | 高 | 高 | 中 | P0 |
| 積分系統 | 高 | 高 | 低 | P0 |
| 等級與徽章 | 中 | 中 | 中 | P1 |
| 動態牆基礎 | 中 | 中 | 中 | P1 |
| 排行榜 | 中 | 低 | 低 | P1 |
| 點讚功能 | 中 | 低 | 低 | P1 |
| 留言功能 | 低 | 低 | 中 | P2 |
| 通知系統 | 低 | 低 | 高 | P2 |
| 好友推薦 | 低 | 低 | 高 | P2 |
| 片單比較 | 低 | 低 | 中 | P2 |
| 私訊功能 | 低 | 低 | 高 | P3 |
| 影評系統 | 低 | 低 | 高 | P3 |

---

## 🎬 結語

這份規劃將 MovieIN 從單純的推薦工具轉型為完整的電影社交平台。透過三階段的漸進式開發，我們可以：

1. **先建立社交基礎**，讓使用者能夠連結和分享
2. **引入遊戲化機制**，提升每日活躍度和留存率
3. **強化互動功能**，打造活躍的社群氛圍

建議從 **Phase 1** 開始，快速驗證市場需求，再根據使用者回饋調整後續方向。

祝 MovieIN 2.0 開發順利！🎉

---

**文檔維護：**
- 下次更新日期：2025-12-12
- 維護者：Mary (Business Analyst)
- 版本歷史：v1.0 (2025-11-12) - 初始版本