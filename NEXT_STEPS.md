# 🚀 MovieIn 下一步執行指南

**更新時間**: 2025-11-11 00:28  
**狀態**: ✅ Merge 完成 + 資料庫擴展完成

---

## ✅ 已完成的工作

1. ✅ **Merge 認證系統** - 成功合併夥伴的分支
2. ✅ **解決所有衝突** - 9 個衝突檔案全部處理完成
3. ✅ **資料庫架構設計** - 創建 9 張表的完整 schema
4. ✅ **Migration 檔案** - `20251111002325_expand_profiles_and_social_tables.py`
5. ✅ **SQLAlchemy Models** - User, Profile, Watchlist, Top10List, Friendship, SharedList, ListInteraction
6. ✅ **文件撰寫** - 完整的架構報告

---

## 🔜 立即要做的事（優先級 P0）

### 1️⃣ 執行資料庫 Migration（5 分鐘）

```powershell
# 確保在專案根目錄
cd c:\Users\User\Desktop\bmad-method

# 進入 backend 目錄
cd backend

# 檢查 Python 環境
python --version

# 安裝/更新 alembic（如果需要）
pip install alembic sqlalchemy psycopg2-binary

# 執行 migration
python -m alembic upgrade head

# 檢查結果
# 應該會看到類似輸出：
# INFO  [alembic.runtime.migration] Running upgrade be60923c8af8 -> 20251111002325, expand_profiles_and_social_tables
```

**預期結果**:
- ✅ profiles 表新增 4 個欄位
- ✅ watchlist 表創建成功
- ✅ top10_list 表創建成功
- ✅ friendships 表創建成功
- ✅ shared_lists 表創建成功
- ✅ list_interactions 表創建成功

**如果遇到錯誤**:
```powershell
# 檢查當前 migration 版本
python -m alembic current

# 查看 migration 歷史
python -m alembic history

# 如果需要回退
python -m alembic downgrade -1
```

---

### 2️⃣ 驗證資料庫連線（2 分鐘）

```powershell
# 在 backend 目錄下
python test_db.py
```

**預期輸出**:
```
✅ Database connection successful!
Tables found: users, profiles, movies, watchlist, top10_list, friendships, shared_lists, list_interactions, ...
```

---

### 3️⃣ 測試前端是否正常（3 分鐘）

```powershell
# 回到專案根目錄
cd ..

# 進入 frontend
cd frontend

# 安裝依賴（如果還沒安裝）
npm install

# 啟動開發伺服器
npm run dev
```

訪問 http://localhost:3000 確認：
- ✅ 首頁 HomeFeed 輪播正常顯示
- ✅ 登入/註冊頁面可訪問
- ✅ Profile 頁面正常（使用新的 ProfileFeed）

---

## 📋 後續開發任務（優先級 P1）

### Phase 1: Watchlist 功能（1-2 天）

#### 後端 API

創建 `backend/app/routers/watchlist.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..models import Watchlist
from ..schemas.watchlist import WatchlistCreate, WatchlistResponse

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

@router.post("/", response_model=WatchlistResponse)
def add_to_watchlist(item: WatchlistCreate, db: Session = Depends(get_db)):
    """加入待看清單"""
    # TODO: 實作
    pass

@router.get("/", response_model=list[WatchlistResponse])
def get_my_watchlist(db: Session = Depends(get_db)):
    """取得我的待看清單"""
    # TODO: 實作
    pass

@router.delete("/{item_id}")
def remove_from_watchlist(item_id: str, db: Session = Depends(get_db)):
    """移除待看清單"""
    # TODO: 實作
    pass
```

#### 前端 UI

在電影卡片上新增按鈕:

```tsx
// frontend/components/MovieCard.tsx
<button 
  onClick={() => addToWatchlist(movie.id)}
  className="btn btn-primary"
>
  + 加入待看
</button>
```

---

### Phase 2: Top 10 List 功能（2-3 天）

#### 後端 API

創建 `backend/app/routers/top10.py`:

```python
@router.post("/", response_model=Top10Response)
def add_to_top10(item: Top10Create, db: Session = Depends(get_db)):
    """加入 Top 10 榜單"""
    pass

@router.get("/", response_model=list[Top10Response])
def get_my_top10(category: str = None, db: Session = Depends(get_db)):
    """取得我的 Top 10"""
    pass

@router.put("/{item_id}/rank")
def update_rank(item_id: str, new_rank: int, db: Session = Depends(get_db)):
    """更新排名"""
    pass
```

#### 前端 UI

在個人檔案頁顯示 Top 10:

```tsx
// frontend/features/profile/Top10Section.tsx
export function Top10Section() {
  // 拖拉排序功能
  // 使用 react-beautiful-dnd 或 @dnd-kit/core
}
```

---

### Phase 3: 好友系統（3-4 天）

#### 後端 API

創建 `backend/app/routers/friends.py`:

```python
@router.post("/invite")
def send_friend_request(friend_email: str, db: Session = Depends(get_db)):
    """發送好友邀請"""
    pass

@router.get("/")
def get_friends(status: str = "accepted", db: Session = Depends(get_db)):
    """取得好友列表"""
    pass

@router.post("/{request_id}/accept")
def accept_friend_request(request_id: str, db: Session = Depends(get_db)):
    """接受好友邀請"""
    pass
```

#### 前端 UI

```tsx
// frontend/app/friends/page.tsx
- 好友列表
- 好友邀請通知
- 搜尋使用者功能
```

---

### Phase 4: 片單分享功能（4-5 天）

#### 後端 API

創建 `backend/app/routers/shared_lists.py`:

```python
@router.post("/")
def create_shared_list(list_data: SharedListCreate, db: Session = Depends(get_db)):
    """創建分享片單"""
    pass

@router.get("/public")
def get_public_lists(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """瀏覽公開片單"""
    pass

@router.post("/{list_id}/like")
def like_list(list_id: str, db: Session = Depends(get_db)):
    """對片單按讚"""
    pass
```

#### 前端 UI

```tsx
// frontend/app/explore/page.tsx
- 公開片單探索頁
- 熱門片單排行
- 片單詳情頁（可按讚、評論）
```

---

## 🧪 測試計畫

### 單元測試

```powershell
# 後端測試
cd backend
pytest tests/

# 前端測試
cd frontend
npm test
```

### 需要測試的功能

1. ✅ 使用者註冊/登入流程
2. ✅ Watchlist CRUD 操作
3. ✅ Top 10 排名更新
4. ✅ 好友邀請流程
5. ✅ 片單分享與互動

---

## 📊 專案檢查清單

### 資料庫（Backend）

- [x] ✅ Migration 檔案創建
- [x] ✅ SQLAlchemy Models 定義
- [ ] ⏳ 執行 `alembic upgrade head`
- [ ] ⏳ 驗證所有表格創建成功
- [ ] ⏳ 創建 Schemas (Pydantic)
- [ ] ⏳ 創建 API Endpoints
- [ ] ⏳ 撰寫單元測試

### 前端（Frontend）

- [x] ✅ Merge 完成（認證系統 + HomeFeed）
- [x] ✅ 路由結構（使用 (app) route group）
- [ ] ⏳ Watchlist UI 元件
- [ ] ⏳ Top 10 UI 元件
- [ ] ⏳ 好友列表頁面
- [ ] ⏳ 片單探索頁面
- [ ] ⏳ API 整合（lib/api.ts）

### 文件

- [x] ✅ 架構報告 (DATABASE_EXPANSION_REPORT.md)
- [x] ✅ 執行指南 (NEXT_STEPS.md)
- [ ] ⏳ API 文件（Swagger/OpenAPI）
- [ ] ⏳ 使用者手冊

---

## 🎯 短期目標（本週）

### Day 1-2: 資料庫與基礎 API
- [ ] 執行 migration
- [ ] 創建 Watchlist API
- [ ] 測試資料庫連線

### Day 3-4: Watchlist 功能
- [ ] 完成 Watchlist 前後端整合
- [ ] 在電影卡片上加入「待看」按鈕
- [ ] 個人檔案頁顯示待看清單

### Day 5-7: Top 10 功能
- [ ] 完成 Top 10 API
- [ ] 實作拖拉排序 UI
- [ ] 個人檔案頁展示 Top 10

---

## 🆘 遇到問題時

### 常見問題 Q&A

**Q1: Migration 執行失敗怎麼辦？**
```powershell
# 檢查錯誤訊息
python -m alembic upgrade head

# 如果是語法錯誤，修正 migration 檔案後重新執行
# 如果是資料庫連線問題，檢查 .env 中的 DATABASE_URL
```

**Q2: 前端無法連接後端？**
```typescript
// 檢查 frontend/.env.local
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000

// 確保後端正在運行
cd backend
uvicorn app.main:app --reload
```

**Q3: 資料表關聯錯誤？**
- 檢查 `backend/app/models/__init__.py` 是否正確導入所有 models
- 確保所有 relationship 的 back_populates 正確配對

---

## 📚 參考資源

### 官方文件
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Alembic Migration](https://alembic.sqlalchemy.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js 14](https://nextjs.org/docs)

### 專案文件
- `docs/architecture.md` - 完整架構文件
- `docs/DATABASE_EXPANSION_REPORT.md` - 資料庫擴展報告
- `backend/app/models/` - 資料模型定義

---

## 🎉 總結

**目前進度**: 🟢 架構完成，準備開始實作

**下一步**: 執行 `alembic upgrade head` 並開始開發 Watchlist API

**預估時間**: 1-2 週完成核心功能

**團隊分工建議**:
- 👨‍💻 你: Watchlist + Top 10 功能
- 👨‍💻 夥伴: 好友系統 + 片單分享

需要任何協助隨時找我！🚀

---

**文件版本**: 1.0  
**作者**: Winston (Architect) 🏗️
