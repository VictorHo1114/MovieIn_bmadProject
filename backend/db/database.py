# app/db/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()  # 讀 backend/.env

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# 建立引擎
# ⚡ 高並發優化：支援 300-500 RPS
# 
# 連線池配置說明：
#   - pool_size=100: 常駐連線池（增加到 100）
#   - max_overflow=200: 峰值時可額外建立 200 個連線（總計 300）
#   - pool_timeout=30: 快速失敗機制（降低等待時間）
#   - pool_pre_ping=True: 自動檢測死連線
#   - pool_recycle=1800: 30分鐘回收連線（更頻繁回收，避免累積）
#   - echo_pool=False: 生產環境關閉日誌（提升性能）
#
# 🎯 效能目標：
#   - 支援 300+ RPS（生產級別）
#   - 平均響應時間 < 100ms（快取命中）
#   - P99 延遲 < 500ms
#   - 快取命中率 > 90%
#
# ⚠️ 注意：
#   1. 確認 Neon 計劃支援 300 concurrent connections
#   2. 生產環境建議使用 PgBouncer 連線池代理
#   3. 關閉 echo_pool 減少 I/O 開銷
engine = create_engine(
    DATABASE_URL,
    pool_size=100,             # 50 → 100 (2x)
    max_overflow=200,          # 100 → 200 (2x)
    pool_timeout=30,           # 60 → 30 (快速失敗)
    pool_pre_ping=True,        # 保持
    pool_recycle=1800,         # 3600 → 1800 (更頻繁回收)
    echo_pool=False            # debug → False (生產優化)
)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 給 model 繼承
#Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
