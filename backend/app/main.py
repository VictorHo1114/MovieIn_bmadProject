from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.home import router as home_router
from app.routers.profile import router as profile_router
from app.routers.search import router as search_router
from db.database import engine
from sqlalchemy import text
from app.routers import simple_recommend_router  # V2 Hybrid Recommendation API

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# 掛載各 router
app.include_router(home_router, prefix="/home", tags=["home"])
app.include_router(profile_router, prefix="/profile", tags=["profile"])
app.include_router(search_router, prefix="/search", tags=["search"])
app.include_router(simple_recommend_router.router)  # V2 Hybrid API ⭐

#測試有沒有連到Neon
@app.get("/db-test")
def db_test():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "✅ Connected to Neon"}
    except Exception as e:
        return {"status": "❌ Failed", "error": str(e)}