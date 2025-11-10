from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# --- 1. 導入所有 routers ---
from app.routers import auth 
from app.routers.home import router as home_router
# (注意：這裡假設你舊的 profile 頁面路由在 profile_page.py 或其他地方)
# from app.routers.profile_page import router as profile_page_router 
from app.routers.search import router as search_router

# [重要修改！] 從 'app.routers.profile' 模組中「導入 router 物件」
from app.routers.profile import router as profile_api_router 

# --- 2. 導入你的 DB engine (只為了 /db-test) ---
from db.database import engine 


app = FastAPI(
    title="MovieIn API",
    description="Backend API for MovieIn Project",
    version="0.1.0"
)

# --- 3. 加入 CORS 中間層 (保持不變) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允許所有來源 (開發時)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. (重要!) 統一定義 API 前綴 ---
API_PREFIX = "/api/v1"

# --- 5. (修改!) 掛載所有 routers ---

app.include_router(auth.router, prefix=API_PREFIX, tags=["Authentication"]) 
app.include_router(profile_api_router, prefix=API_PREFIX, tags=["Profile"]) # [新增！] (這行現在正確了)

app.include_router(home_router, prefix=f"{API_PREFIX}/home", tags=["home"])
# app.include_router(profile_page_router, prefix=f"{API_PREFIX}/profile", tags=["profile_page"]) 
app.include_router(search_router, prefix=f"{API_PREFIX}/search", tags=["search"])
from app.routers.movie import router as movie_router
app.include_router(movie_router, prefix="/movie", tags=["movie"])
from app.routers.popular import router as popular_router
app.include_router(popular_router)


# --- 6. 你的測試路由 (保持不變) ---
@app.get("/db-test")
def db_test():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "✅ Connected to Neon"}
    except Exception as e:
        return {"status": "❌ Failed", "error": str(e)}

# 根路由 (可選)
@app.get("/")
def read_root():
    return {"message": "Welcome to MovieIn API"}