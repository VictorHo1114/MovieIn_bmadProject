# MovieIn Use Case 完整實作規劃

## 文件資訊
**建立日期**: 2025-11-06  
**作者**: Winston (Architect)  
**版本**: 1.0  
**專案**: MovieIn - AI 電影推薦平台

---

## 執行摘要

本文件針對 MovieIn 專案的三大核心 Use Case 進行完整的 Gap 分析與實作規劃：

- **A. Recommendation 頁面（推薦頁）** - 5 個需求
- **B. Auth / Profile 設定頁面** - 6 個需求  
- **C. Search Page（電影查詢頁）** - 5 個需求

**總計**: 16 個功能需求，預估開發時間 **4-6 週**（1 位全端工程師）

---

# 第一部分：Gap 分析與優先級

##  現況評估表

| 領域 | 已完成 | 待完成 | 完成度 | 優先級 |
|------|--------|--------|--------|--------|
| **推薦引擎** | 後端 API | 前端整合 + 電影卡 UI | 70% |  P0 |
| **認證系統** | 使用者模型 | 完整 Auth 流程 | 20% |  P0 |
| **Profile 管理** | 基礎 Schema | 片單功能 + CRUD | 10% |  P1 |
| **搜尋功能** | Mock API | 真實搜尋 + 進階篩選 | 5% |  P1 |
| **電影卡 UI/UX** | 基礎元件 | 正反面翻轉 + 互動 | 30% |  P0 |

---

##  優先級定義

###  P0 - 核心 MVP（必須先完成）
1. **認證系統** - 無登入就無法使用其他功能
2. **推薦頁面完整流程** - 這是產品的核心價值
3. **電影卡 UI** - 使用者體驗的關鍵

###  P1 - 重要功能（第二階段）
4. **Profile 片單管理** - 增加使用者黏著度
5. **搜尋功能** - 提供另一個探索電影的方式

###  P2 - 增強功能（第三階段）
6. **進階篩選** - 提升搜尋精確度
7. **自動完成** - 改善搜尋體驗

---

# 第二部分：詳細實作規劃

## A. Recommendation 頁面（推薦頁）

### 需求 A1: 登入後進入推薦頁，顯示標籤與輸入 bar

#### 現況
-  `HomeClient.tsx` 已有基礎 UI
-  Feature labels 已定義在 `intent_labels.py`
-  缺少登入驗證
-  未整合到推薦頁路由

#### 需要新增/修改的檔案

**1. 前端 - 新增推薦頁面路由**
```
frontend/app/recommend/page.tsx (新增)
frontend/features/recommend/RecommendClient.tsx (重構自 HomeClient)
frontend/features/recommend/services.ts (新增)
```

**2. 前端 - 認證中介層**
```
frontend/middleware.ts (新增) - Next.js middleware 驗證登入狀態
frontend/lib/auth.ts (新增) - 認證工具函式
```

**實作步驟**:
```typescript
// Step 1: 建立 middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth_token');
  
  // 如果訪問受保護路由但未登入，重定向到登入頁
  if (!token && request.nextUrl.pathname.startsWith('/recommend')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/recommend/:path*', '/profile/:path*']
};
```

```typescript
// Step 2: 建立 app/recommend/page.tsx
import { RecommendClient } from '@/features/recommend/RecommendClient';

export default function RecommendPage() {
  return <RecommendClient />;
}
```

```typescript
// Step 3: 重構 RecommendClient.tsx
// 從 HomeClient.tsx 移植並增強
// - 增加載入狀態（skeleton）
// - 優化 3 秒內渲染（lazy loading, code splitting）
```

**AC 驗證清單**:
- [ ] 未登入訪問 `/recommend` 自動重定向到 `/login`
- [ ] 已登入可看到至少 5 個 feature_label 按鈕
- [ ] 有一個自然語言輸入 bar
- [ ] 頁面在 3 秒內完成首次渲染（Network: Fast 3G 模擬）

---

### 需求 A2: Generate 後顯示 5 個電影推薦卡

#### 現況
-  後端 API `/api/recommend/movies` 已實作
-  回傳 `FrontendMovie[]` 格式
-  前端未呼叫此 API
-  缺少電影卡元件

#### 需要新增/修改的檔案

**1. 前端 - API 整合**
```
frontend/lib/api.ts (修改) - 新增 recommendMovies 方法
frontend/lib/types/movie.ts (修改) - 新增 FrontendMovie 型別
```

**2. 前端 - 電影卡元件**
```
frontend/components/MovieCard.tsx (新增)
frontend/components/MovieCardSkeleton.tsx (新增) - 載入骨架
```

**實作步驟**:

```typescript
// Step 1: 修改 lib/api.ts
export const Api = {
  // ...existing methods
  
  recommend: {
    // 解析意圖
    parseIntent: (payload: {
      text: string;
      preselected_labels: string[];
    }) => postJSON<MovieIntent>('/api/intent/parse', payload),
    
    // 取得推薦
    getMovies: (intent: MovieIntent) => 
      postJSON<FrontendMovie[]>('/api/recommend/movies', intent),
  },
};
```

```typescript
// Step 2: 新增 types/movie.ts
export interface FrontendMovie {
  id: number;
  title: string;
  overview: string;
  poster_url: string | null;
  release_year: number | null;
  vote_average: number;
}

export interface MovieCardData extends FrontendMovie {
  reason_snippet?: string; // A4 需求
}
```

```typescript
// Step 3: 建立 components/MovieCard.tsx
'use client';

import { useState } from 'react';
import { Card } from '@/components/figmaAi_ui/card';
import { Button } from '@/components/figmaAi_ui/button';
import { BookmarkIcon, HeartIcon } from 'lucide-react';

interface MovieCardProps {
  movie: MovieCardData;
  onAddToWatchlist: (movieId: number) => void;
  onAddToTop10: (movieId: number) => void;
}

export function MovieCard({ movie, onAddToWatchlist, onAddToTop10 }: MovieCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);
  
  return (
    <Card className="movie-card">
      {/* 正面 */}
      {!isFlipped && (
        <div className="card-front">
          <img src={movie.poster_url} alt={movie.title} />
          <h3>{movie.title}</h3>
          {movie.reason_snippet && (
            <p className="reason">{movie.reason_snippet}</p>
          )}
          <Button onClick={() => setIsFlipped(true)}>Flip</Button>
        </div>
      )}
      
      {/* 反面 */}
      {isFlipped && (
        <div className="card-back">
          <p>{movie.overview}</p>
          <div className="actions">
            <Button onClick={() => onAddToWatchlist(movie.id)}>
              <BookmarkIcon /> 待看
            </Button>
            <Button onClick={() => onAddToTop10(movie.id)}>
              <HeartIcon /> Top 10
            </Button>
          </div>
          <Button onClick={() => setIsFlipped(false)}>Back</Button>
        </div>
      )}
    </Card>
  );
}
```

```typescript
// Step 4: 在 RecommendClient.tsx 中整合
const [movies, setMovies] = useState<MovieCardData[]>([]);
const [isGenerating, setIsGenerating] = useState(false);

const handleGenerate = async () => {
  setIsGenerating(true);
  
  try {
    // 1. 解析意圖
    const intent = await Api.recommend.parseIntent({
      text: naturalLanguageInput,
      preselected_labels: [...selectedLabels]
    });
    
    // 2. 取得推薦
    const recommendations = await Api.recommend.getMovies(intent);
    
    // 3. 更新狀態
    setMovies(recommendations.slice(0, 5)); // 確保只顯示 5 個
  } catch (error) {
    console.error('推薦失敗:', error);
    // 顯示錯誤訊息
  } finally {
    setIsGenerating(false);
  }
};

return (
  <div>
    {/* ... 標籤選擇區 ... */}
    
    <Button onClick={handleGenerate} disabled={isGenerating}>
      {isGenerating ? 'Generating...' : ' Generate'}
    </Button>
    
    <div className="movie-grid">
      {isGenerating ? (
        // 載入骨架
        Array(5).fill(0).map((_, i) => <MovieCardSkeleton key={i} />)
      ) : (
        // 電影卡
        movies.map(movie => (
          <MovieCard 
            key={movie.id} 
            movie={movie}
            onAddToWatchlist={handleAddToWatchlist}
            onAddToTop10={handleAddToTop10}
          />
        ))
      )}
    </div>
  </div>
);
```

**AC 驗證清單**:
- [ ] 點擊 Generate 後在 3 秒內顯示結果（Network: Fast 3G）
- [ ] 顯示恰好 5 個電影卡
- [ ] 電影卡符合 UI/UX 設計稿（需設計師確認）
- [ ] 推薦結果符合標籤與自然語言（抽樣測試 10 次）

---

### 需求 A3: 電影卡內標記收藏至待看/Top10 清單

#### 現況
-  User 模型已存在
-  缺少 `watchlist` 和 `top10` 資料表
-  缺少收藏 API

#### 需要新增/修改的檔案

**1. 後端 - 資料庫 Schema**
```
backend/app/models/movie.py (新增)
backend/app/models/watchlist.py (新增)
backend/db/versions/xxx_add_movie_lists.py (新增 migration)
```

**2. 後端 - API 端點**
```
backend/app/routers/favorites.py (新增)
backend/app/schemas/favorites.py (新增)
```

**實作步驟**:

```python
# Step 1: 建立 Movie 模型 (models/movie.py)
from sqlalchemy import Column, Integer, String, Text, Float
from .base import Base

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True)  # TMDB ID
    title = Column(String, nullable=False)
    overview = Column(Text)
    poster_url = Column(String)
    release_year = Column(Integer)
    vote_average = Column(Float)
    
    # 快取 TMDB 資料，避免重複查詢
```

```python
# Step 2: 建立關聯表 (models/watchlist.py)
from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, text, Enum
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import enum

class ListType(str, enum.Enum):
    WATCHLIST = "watchlist"
    TOP10 = "top10"

class UserMovieList(Base):
    __tablename__ = "user_movie_lists"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), primary_key=True)
    list_type = Column(Enum(ListType), primary_key=True)
    added_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
```

```python
# Step 3: 建立 migration
# 執行: alembic revision --autogenerate -m "add movie lists"
# 檢查生成的 migration 檔案是否正確
```

```python
# Step 4: 建立 API (routers/favorites.py)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import SessionLocal
from app.models.user import User
from app.models.movie import Movie
from app.models.watchlist import UserMovieList, ListType

router = APIRouter(prefix="/api/favorites", tags=["favorites"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/watchlist/{movie_id}")
async def add_to_watchlist(
    movie_id: int,
    user_id: str,  # TODO: 從 auth token 取得
    db: Session = Depends(get_db)
):
    # 1. 確保 movie 存在於本地 DB（若無則從 TMDB 抓取並建立）
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        # TODO: 從 TMDB API 抓取電影資料並建立
        pass
    
    # 2. 新增至待看清單
    list_item = UserMovieList(
        user_id=user_id,
        movie_id=movie_id,
        list_type=ListType.WATCHLIST
    )
    db.add(list_item)
    db.commit()
    
    return {"status": "success", "message": "已加入待看清單"}

@router.post("/top10/{movie_id}")
async def add_to_top10(
    movie_id: int,
    user_id: str,
    db: Session = Depends(get_db)
):
    # 1. 檢查 Top10 是否已滿（最多 10 部）
    count = db.query(UserMovieList).filter(
        UserMovieList.user_id == user_id,
        UserMovieList.list_type == ListType.TOP10
    ).count()
    
    if count >= 10:
        raise HTTPException(
            status_code=400, 
            detail="Top10 清單已滿，請先移除其他電影"
        )
    
    # 2. 新增至 Top10
    list_item = UserMovieList(
        user_id=user_id,
        movie_id=movie_id,
        list_type=ListType.TOP10
    )
    db.add(list_item)
    db.commit()
    
    return {"status": "success", "message": "已加入 Top10"}

@router.delete("/{list_type}/{movie_id}")
async def remove_from_list(
    list_type: ListType,
    movie_id: int,
    user_id: str,
    db: Session = Depends(get_db)
):
    db.query(UserMovieList).filter(
        UserMovieList.user_id == user_id,
        UserMovieList.movie_id == movie_id,
        UserMovieList.list_type == list_type
    ).delete()
    db.commit()
    
    return {"status": "success"}
```

**3. 前端 - Optimistic UI 更新**

```typescript
// frontend/lib/api.ts
export const Api = {
  favorites: {
    addToWatchlist: (movieId: number) => 
      postJSON('/api/favorites/watchlist/' + movieId, {}),
    
    addToTop10: (movieId: number) => 
      postJSON('/api/favorites/top10/' + movieId, {}),
    
    remove: (listType: 'watchlist' | 'top10', movieId: number) =>
      deleteJSON(`/api/favorites/${listType}/${movieId}`),
  },
};
```

```typescript
// RecommendClient.tsx - Optimistic Update
const [favoriteStates, setFavoriteStates] = useState<{
  [movieId: number]: {
    inWatchlist: boolean;
    inTop10: boolean;
  }
}>({});

const handleAddToWatchlist = async (movieId: number) => {
  // 1. Optimistic update - 立即更新 UI
  setFavoriteStates(prev => ({
    ...prev,
    [movieId]: { ...prev[movieId], inWatchlist: true }
  }));
  
  try {
    // 2. 呼叫後端 API
    await Api.favorites.addToWatchlist(movieId);
    
    // 3. 顯示成功提示
    toast.success('已加入待看清單');
  } catch (error) {
    // 4. 失敗則回滾 UI
    setFavoriteStates(prev => ({
      ...prev,
      [movieId]: { ...prev[movieId], inWatchlist: false }
    }));
    
    toast.error('加入失敗，請重試');
  }
};
```

**AC 驗證清單**:
- [ ] 點擊「待看」按鈕後 UI 立即更新（< 100ms）
- [ ] 後端成功則保持狀態，失敗則回滾 UI
- [ ] Profile 頁面可看到更新後的清單
- [ ] 資料庫正確儲存收藏記錄

---

### 需求 A4: 顯示推薦理由（reason_snippet）與翻卡詳細資訊

#### 現況
-  後端未生成 `reason_snippet`
-  前端電影卡缺少翻轉動畫

#### 需要新增/修改的檔案

**1. 後端 - 生成推薦理由**
```
backend/app/routers/recommend_router.py (修改)
backend/app/schemas/movie_result.py (修改)
```

**實作步驟**:

```python
# Step 1: 修改 movie_result.py
class FrontendMovie(BaseModel):
    id: int
    title: str
    overview: str
    poster_url: Optional[str] = None
    release_year: Optional[int] = None
    vote_average: float = Field(0.0)
    reason_snippet: Optional[str] = None  # 新增欄位
```

```python
# Step 2: 在 recommend_router.py 生成理由
def generate_reason_snippet(movie: Dict, intent: MovieIntent) -> str:
    """
    根據 intent 生成推薦理由
    """
    reasons = []
    
    # 檢查類型匹配
    if intent.constraints and intent.constraints.genres:
        movie_genres = movie.get("genre_ids", [])
        matched_genres = [
            genre for genre in intent.constraints.genres
            if GENRE_TO_TMDB.get(genre) in movie_genres
        ]
        if matched_genres:
            reasons.append(f"符合 {', '.join(matched_genres)} 類型")
    
    # 檢查年份
    if intent.constraints and intent.constraints.year_range:
        year = int(movie.get("release_date", "")[:4])
        if year:
            reasons.append(f"{year} 年作品")
    
    # 檢查評分
    vote_avg = movie.get("vote_average", 0)
    if vote_avg >= 8.0:
        reasons.append("高評分佳作")
    
    return "  ".join(reasons[:3])  # 最多顯示 3 個理由

@router.post("/movies", response_model=List[FrontendMovie])
async def get_movie_recommendations(intent: MovieIntent = Body(...)):
    # ...existing code...
    
    # 在格式化結果時加入 reason_snippet
    formatted_movies = []
    for movie in raw_data["results"][:movie_count]:
        f_movie = FrontendMovie(
            id=movie.get("id"),
            title=movie.get("title", "No Title"),
            overview=movie.get("overview", ""),
            poster_url=_build_poster_url(movie.get("poster_path")),
            release_year=_parse_release_year(movie.get("release_date")),
            vote_average=movie.get("vote_average", 0.0),
            reason_snippet=generate_reason_snippet(movie, intent)  # 新增
        )
        formatted_movies.append(f_movie)
    
    return formatted_movies
```

**2. 前端 - 電影卡翻轉動畫**

```css
/* components/MovieCard.css */
.movie-card {
  position: relative;
  width: 300px;
  height: 450px;
  perspective: 1000px;
}

.card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.6s;
  transform-style: preserve-3d;
}

.movie-card.flipped .card-inner {
  transform: rotateY(180deg);
}

.card-front, .card-back {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.card-back {
  transform: rotateY(180deg);
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}
```

```typescript
// components/MovieCard.tsx (完整版)
export function MovieCard({ movie, onAddToWatchlist, onAddToTop10 }: MovieCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);
  
  return (
    <div className={`movie-card ${isFlipped ? 'flipped' : ''}`}>
      <div className="card-inner">
        {/* 正面 */}
        <div className="card-front">
          <img 
            src={movie.poster_url || '/placeholder-poster.jpg'} 
            alt={movie.title}
            className="poster"
          />
          <div className="card-front-content">
            <h3 className="title">{movie.title}</h3>
            <div className="meta">
              <span className="year">{movie.release_year}</span>
              <span className="rating"> {movie.vote_average.toFixed(1)}</span>
            </div>
            {movie.reason_snippet && (
              <p className="reason-snippet">
                 {movie.reason_snippet}
              </p>
            )}
            <Button 
              onClick={() => setIsFlipped(true)}
              className="flip-button"
            >
              查看詳情 
            </Button>
          </div>
        </div>
        
        {/* 反面 */}
        <div className="card-back">
          <h3>{movie.title}</h3>
          <p className="overview">{movie.overview}</p>
          
          <div className="detailed-info">
            <div className="info-row">
              <span className="label">年份：</span>
              <span>{movie.release_year}</span>
            </div>
            <div className="info-row">
              <span className="label">評分：</span>
              <span> {movie.vote_average.toFixed(1)} / 10</span>
            </div>
          </div>
          
          <div className="actions">
            <Button 
              onClick={() => onAddToWatchlist(movie.id)}
              variant="outline"
            >
              <BookmarkIcon size={16} /> 待看
            </Button>
            <Button 
              onClick={() => onAddToTop10(movie.id)}
              variant="outline"
            >
              <HeartIcon size={16} /> Top 10
            </Button>
          </div>
          
          <Button 
            onClick={() => setIsFlipped(false)}
            className="back-button"
            variant="ghost"
          >
             返回
          </Button>
        </div>
      </div>
    </div>
  );
}
```

**AC 驗證清單**:
- [ ] 電影卡正面顯示 reason_snippet（若存在）
- [ ] 點擊「查看詳情」觸發 3D 翻轉動畫（0.6s）
- [ ] 反面顯示完整資訊（劇情、年份、評分）
- [ ] 反面包含「待看」和「Top10」按鈕
- [ ] 設計師確認 UI 符合設計稿

---

## B. Auth / Profile 設定頁面

### 需求 B1-B2: 註冊、登入、登出

#### 實作步驟

**1. 後端 - 認證系統**

```python
# backend/app/routers/auth.py (新增)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 密碼雜湊
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 設定
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Schemas
class SignupRequest(BaseModel):
    email: EmailStr
    password: str  # 前端應驗證長度 >= 8
    username: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Utility functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Routes
@router.post("/signup", response_model=TokenResponse)
async def signup(req: SignupRequest, db: Session = Depends(get_db)):
    # 1. 檢查 email 是否已存在
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email 已被註冊")
    
    # 2. 建立使用者
    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        username=req.username
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 3. 生成 token
    token = create_access_token({"sub": str(user.id), "email": user.email})
    
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 1. 查找使用者
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤"
        )
    
    # 2. 生成 token
    token = create_access_token({"sub": str(user.id), "email": user.email})
    
    return TokenResponse(access_token=token)

@router.post("/logout")
async def logout():
    # 客戶端負責刪除 token
    return {"status": "success", "message": "已登出"}
```

**2. 前端 - 認證頁面**

```typescript
// frontend/app/login/page.tsx (新增)
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/figmaAi_ui/button';
import { Input } from '@/components/figmaAi_ui/input';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          username: email,  // OAuth2 spec uses "username"
          password: password
        })
      });
      
      if (!response.ok) throw new Error('登入失敗');
      
      const data = await response.json();
      
      // 儲存 token
      localStorage.setItem('auth_token', data.access_token);
      document.cookie = `auth_token=${data.access_token}; path=/; max-age=${60*60*24}`;
      
      // 重定向到推薦頁
      router.push('/recommend');
    } catch (error) {
      alert('登入失敗，請檢查帳號密碼');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="login-page">
      <form onSubmit={handleLogin}>
        <h1>登入 MovieIn</h1>
        
        <Input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        
        <Input
          type="password"
          placeholder="密碼"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        
        <Button type="submit" disabled={isLoading}>
          {isLoading ? '登入中...' : '登入'}
        </Button>
        
        <p>
          還沒有帳號？ <a href="/signup">註冊</a>
        </p>
      </form>
    </div>
  );
}
```

```typescript
// frontend/app/signup/page.tsx (新增)
// 類似 login，但多驗證：
// - Email 格式
// - 密碼長度 >= 8
// - 密碼確認
```

**AC 驗證清單**:
- [ ] 註冊時驗證 email 格式與密碼長度
- [ ] 密碼以 bcrypt 雜湊儲存
- [ ] 登入成功回傳 JWT token
- [ ] 登入失敗回傳 401
- [ ] 登出清除 token 並重定向

---

### 需求 B3-B5: Profile 編輯與片單管理

#### 實作步驟

**1. 後端 - Profile API**

```python
# backend/app/routers/profile.py (修改)
@router.get("/me")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 取得待看清單
    watchlist = db.query(Movie).join(UserMovieList).filter(
        UserMovieList.user_id == current_user.id,
        UserMovieList.list_type == ListType.WATCHLIST
    ).all()
    
    # 取得 Top10
    top10 = db.query(Movie).join(UserMovieList).filter(
        UserMovieList.user_id == current_user.id,
        UserMovieList.list_type == ListType.TOP10
    ).all()
    
    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username
        },
        "watchlist": [format_movie(m) for m in watchlist],
        "top10": [format_movie(m) for m in top10]
    }

@router.put("/me")
async def update_profile(
    updates: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if updates.username:
        current_user.username = updates.username
    # ...其他欄位
    
    db.commit()
    return {"status": "success"}

@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 驗證舊密碼
    if not verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=403, detail="舊密碼錯誤")
    
    # 更新密碼
    current_user.password_hash = hash_password(req.new_password)
    db.commit()
    
    return {"status": "success"}

@router.delete("/me")
async def delete_account(
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 驗證密碼
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(status_code=403, detail="密碼錯誤")
    
    # 刪除所有相關資料
    db.query(UserMovieList).filter(UserMovieList.user_id == current_user.id).delete()
    db.delete(current_user)
    db.commit()
    
    return {"status": "success"}
```

**2. 前端 - Profile 頁面**

```typescript
// frontend/app/profile/page.tsx
export default function ProfilePage() {
  return (
    <div className="profile-page">
      <h1>我的 Profile</h1>
      
      {/* 使用者資訊 */}
      <ProfileInfo />
      
      {/* 待看清單 */}
      <section>
        <h2>待看清單</h2>
        <MovieList type="watchlist" />
      </section>
      
      {/* Top10 */}
      <section>
        <h2>我的 Top 10</h2>
        <MovieList type="top10" />
      </section>
      
      {/* 設定 */}
      <section>
        <h2>帳號設定</h2>
        <ChangePasswordForm />
        <DeleteAccountButton />
      </section>
    </div>
  );
}
```

**AC 驗證清單**:
- [ ] Profile 頁面顯示使用者資訊
- [ ] 待看清單和 Top10 正確顯示
- [ ] 可編輯 username 等資訊
- [ ] 更改密碼需驗證舊密碼
- [ ] 刪除帳號需二次確認
- [ ] 片單可刪除電影

---

## C. Search Page（電影查詢頁）

### 需求 C1-C5: 搜尋功能完整實作

#### 實作步驟

**1. 後端 - 搜尋 API**

```python
# backend/app/routers/search.py (修改)
@router.get("")
async def search_movies(
    q: str = Query(..., min_length=1),
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    genre: Optional[str] = None,
    language: Optional[str] = None,
    page: int = Query(1, ge=1)
):
    # 呼叫 TMDB Search API
    params = {
        "api_key": TMDB_API_KEY,
        "query": q,
        "page": page
    }
    
    if year_from:
        params["primary_release_date.gte"] = f"{year_from}-01-01"
    if year_to:
        params["primary_release_date.lte"] = f"{year_to}-12-31"
    # ...其他篩選
    
    response = await httpx.get("https://api.themoviedb.org/3/search/movie", params=params)
    data = response.json()
    
    return {
        "results": [format_movie(m) for m in data["results"]],
        "total_results": data["total_results"],
        "page": page
    }

@router.get("/suggestions")
async def get_suggestions(q: str = Query(..., min_length=2)):
    # 實作自動完成
    # 可使用 TMDB /search/movie 或本地快取
    pass
```

**2. 前端 - 搜尋頁面**

```typescript
// frontend/app/search/page.tsx
export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [filters, setFilters] = useState({});
  
  return (
    <div className="search-page">
      {/* 搜尋 bar + 自動完成 */}
      <SearchBar 
        value={query}
        onChange={setQuery}
        onSearch={handleSearch}
      />
      
      {/* 進階篩選 */}
      <FilterPanel 
        filters={filters}
        onChange={setFilters}
      />
      
      {/* 搜尋結果 */}
      <SearchResults results={results} />
      
      {/* 分頁 */}
      <Pagination />
    </div>
  );
}
```

**AC 驗證清單**:
- [ ] 輸入關鍵字後顯示相關電影
- [ ] 支援年份、類型、語言篩選
- [ ] 自動完成功能（debounce 300ms）
- [ ] 無結果時顯示建議
- [ ] TMDB API 錯誤時顯示友善訊息

---

# 第三部分：開發排程與資源分配

## 開發階段規劃（4-6 週）

### 第一階段：核心 MVP（2 週） P0

**Week 1:**
- Day 1-2: 認證系統（註冊、登入、JWT）
- Day 3-4: 資料庫 Schema（Movie, UserMovieList）
- Day 5: 認證 middleware 與前端整合

**Week 2:**
- Day 1-2: 電影卡元件（正反面 UI）
- Day 3-4: 推薦頁面完整流程
- Day 5: 收藏功能（API + Optimistic UI）

### 第二階段：重要功能（1.5 週） P1

**Week 3:**
- Day 1-2: Profile 頁面與片單管理
- Day 3-4: 搜尋功能基礎版本
- Day 5: 整合測試與 Bug 修復

### 第三階段：增強功能（1.5 週） P2

**Week 4-5:**
- Day 1-2: 進階搜尋篩選
- Day 3: 自動完成功能
- Day 4-5: UI/UX 優化與效能調整

### 第四階段：測試與部署（1 週）

**Week 6:**
- Day 1-3: QA 測試與修復
- Day 4: 部署準備（環境變數、CORS 設定）
- Day 5: 上線與監控

---

## 技術風險與緩解策略

| 風險 | 影響 | 機率 | 緩解策略 |
|------|------|------|----------|
| TMDB API Rate Limit | 高 | 中 | 實作快取層（Redis） |
| 前端效能（3秒目標） | 中 | 中 | Code splitting, lazy loading, CDN |
| 認證安全性 | 高 | 低 | 使用成熟套件（passlib, jose），定期更新 |
| 資料庫遷移失敗 | 中 | 低 | 完整的 migration 測試，保留回滾方案 |

---

## 成功指標（KPIs）

### 功能完成度
- [ ] 16 個 AC 全部通過
- [ ] 無 P0/P1 級別 Bug

### 效能指標
- [ ] 推薦頁面首次渲染 < 3 秒（Fast 3G）
- [ ] 搜尋結果渲染 < 3 秒
- [ ] Optimistic UI 更新 < 100ms

### 品質指標
- [ ] 單元測試覆蓋率 > 60%（核心邏輯）
- [ ] E2E 測試覆蓋主要流程
- [ ] 無安全漏洞（OWASP Top 10）

---

## 附錄：完整檔案清單

### 需要新增的檔案（30+）

**後端（15 個）:**
1. `backend/app/routers/auth.py`
2. `backend/app/routers/favorites.py`
3. `backend/app/models/movie.py`
4. `backend/app/models/watchlist.py`
5. `backend/app/schemas/auth.py`
6. `backend/app/schemas/favorites.py`
7. `backend/db/versions/xxx_add_movie_lists.py`
8. `backend/app/utils/auth.py`（JWT helpers）
9. `backend/.env.example`
10. ...（其他輔助檔案）

**前端（15 個）:**
1. `frontend/app/login/page.tsx`
2. `frontend/app/signup/page.tsx`
3. `frontend/app/recommend/page.tsx`
4. `frontend/app/search/page.tsx`
5. `frontend/middleware.ts`
6. `frontend/lib/auth.ts`
7. `frontend/components/MovieCard.tsx`
8. `frontend/components/MovieCard.css`
9. `frontend/features/recommend/RecommendClient.tsx`
10. `frontend/features/profile/ProfilePage.tsx`
11. ...（其他元件）

### 需要修改的檔案（10+）

1. `backend/app/main.py` - 掛載新 routers
2. `backend/app/routers/recommend_router.py` - 加入 reason_snippet
3. `frontend/lib/api.ts` - 新增 API 方法
4. `frontend/lib/types/movie.ts` - 新增型別定義
5. ...

---

**文件結束**

預估總開發時間：**4-6 週**（1 位全端工程師）  
核心 MVP 時間：**2 週**

若有疑問或需要更詳細的實作指引，請隨時詢問！ 
