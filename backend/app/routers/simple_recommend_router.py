# backend/app/routers/simple_recommend_router.py
"""
智能混合推薦 Router (Feature + Embedding)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from db.database import SessionLocal, get_db
from app.services.simple_recommend import (
    recommend_movies_hybrid, 
    recommend_movies_simple,
    recommend_movies_embedding_first  # 新增 Phase 3.6 ⭐
)
from app.services.mapping_tables import get_mood_label_list  # 修改導入 ⭐

router = APIRouter(prefix="/api/recommend/v2", tags=["recommend-v2"])

class SimpleRecommendRequest(BaseModel):
    query: str
    selected_genres: Optional[List[str]] = None  # 類型標籤 (繁體中文)
    selected_moods: Optional[List[str]] = None   # 心情/情境標籤
    selected_eras: Optional[List[str]] = None    # 年代標籤 (如 ["90s", "00s"]) ⭐
    randomness: Optional[float] = 0.3            # 隨機性參數（0.0-1.0）
    decision_threshold: Optional[int] = 40       # 決策閾值（預設 40）
    use_legacy: Optional[bool] = False           # 是否使用舊版推薦（對照組）
    use_phase36: Optional[bool] = False          # 是否使用 Phase 3.6 Embedding-First ⭐ 新增

@router.post("/movies")
async def get_simple_recommendations(
    request: SimpleRecommendRequest,
    db: Session = Depends(get_db)
):
    """
    智能混合推薦 API (Feature + Embedding 自動切換)
    
    流程：
    1. Feature Extraction: 解析自然語言 + Mood Buttons
    2. SQL Feature Matching: 快速候選檢索
    3. 智能判斷: 6 維評分系統決定路徑
    4. Feature/Embedding: 根據評分選擇最佳策略
    5. 多樣性過濾: 確保推薦多樣性
    
    參數：
    - query: 自然語言查詢（如 "007"、"溫暖治癒的超級英雄電影"）
    - selected_moods: 心情/情境標籤（如 ["動作冒險", "視覺饗宴"]）
    - selected_genres: 類型標籤（如 ["Action", "Science Fiction"]）
    - randomness: 隨機性（0.0 = 完全確定，1.0 = 完全隨機，預設 0.3）
    - decision_threshold: 決策閾值（預設 40，越高越傾向 Embedding）
    - use_legacy: 是否使用舊版推薦（預設 False，供 A/B 測試）
    - use_phase36: 是否使用 Phase 3.6 Embedding-First（預設 False，新架構）⭐
    
    返回：
    - movies: 推薦電影列表（包含 similarity_score 或 feature_score）
    - strategy: 使用的推薦策略（"Feature" 或 "Embedding" 或 "Phase36"）
    - decision_score: 決策評分（供調試用）
    """
    try:
        # ⭐ Phase 3.6: Embedding-First 架構
        if request.use_phase36:
            # 將 selected_eras 轉換為 year_ranges
            from app.services.enhanced_feature_extraction import ERA_RANGE_MAP
            year_ranges = None
            if request.selected_eras:
                year_ranges = [ERA_RANGE_MAP.get(era, [2000, 2009]) for era in request.selected_eras]
            
            results = await recommend_movies_embedding_first(
                natural_query=request.query or "",
                mood_labels=request.selected_moods or [],
                genres=request.selected_genres or [],
                year_ranges=year_ranges,
                db_session=db,
                count=10
            )
            
            return {
                "success": True,
                "query": request.query,
                "count": len(results),
                "movies": results,
                "strategy": "Phase36-EmbeddingFirst",
                "version": "3.6",
                "config": {
                    "architecture": "Embedding-First",
                    "primary_engine": "Embedding Similarity Search",
                    "secondary_engine": "Feature Filtering",
                    "quadrants": 3
                }
            }
        
        # 如果請求使用舊版推薦（對照組）
        if request.use_legacy:
            results = await recommend_movies_simple(
                user_input=request.query,
                db_session=db,
                count=10,
                selected_genres=request.selected_genres,
                selected_moods=request.selected_moods
            )
            
            return {
                "success": True,
                "query": request.query,
                "count": len(results),
                "movies": results,
                "strategy": "Legacy",
                "decision_score": None
            }
        
        # 使用新版智能混合推薦 (Phase 3.5)
        results = await recommend_movies_hybrid(
            user_input=request.query,
            db_session=db,
            count=10,
            selected_moods=request.selected_moods,
            selected_genres=request.selected_genres,
            selected_eras=request.selected_eras,  # 新增 ⭐
            randomness=request.randomness or 0.3,
            decision_threshold=request.decision_threshold or 40
        )
        
        # 從結果推斷使用的策略
        if results and len(results) > 0:
            first_movie = results[0]
            if first_movie.get("similarity_score", 0) > 0:
                strategy = "Embedding"
            elif first_movie.get("feature_score", 0) > 0:
                strategy = "Feature"
            else:
                strategy = "Unknown"
        else:
            strategy = "None"
        
        return {
            "success": True,
            "query": request.query,
            "count": len(results),
            "movies": results,
            "strategy": strategy,
            "config": {
                "randomness": request.randomness or 0.3,
                "decision_threshold": request.decision_threshold or 40
            }
        }
        
    except Exception as e:
        print(f"[Error] 推薦失敗: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mood-labels")
async def get_mood_labels():
    """
    獲取所有可用的 Mood Labels
    
    返回格式：
    [
        {"id": "失戀", "description": "心碎、需要療癒", "category": "情緒"},
        {"id": "派對", "description": "與朋友一起看、氣氛熱鬧", "category": "情境"},
        ...
    ]
    """
    try:
        labels = get_mood_label_list()
        return {
            "success": True,
            "count": len(labels),
            "labels": labels
        }
    except Exception as e:
        print(f"[Error] 獲取 Mood Labels 失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-info")
async def get_system_info():
    """
    獲取混合推薦系統資訊
    
    返回系統配置、評分權重、閾值等資訊
    """
    from app.services.simple_recommend import HYBRID_CONFIG
    from app.services.enhanced_feature_extraction import (
        ERA_RANGE_MAP,
        GENRE_SIMPLIFIED_TO_TRADITIONAL
    )
    
    return {
        "success": True,
        "system": "Hybrid Recommendation System (Feature + Embedding)",
        "version": "2.0",
        "config": HYBRID_CONFIG,
        "filter_options": {
            "eras": [
                {"id": "60s", "label": "60年代", "range": [1960, 1969]},
                {"id": "70s", "label": "70年代", "range": [1970, 1979]},
                {"id": "80s", "label": "80年代", "range": [1980, 1989]},
                {"id": "90s", "label": "90年代", "range": [1990, 1999]},
                {"id": "00s", "label": "00年代", "range": [2000, 2009]},
                {"id": "10s", "label": "10年代", "range": [2010, 2019]},
                {"id": "20s", "label": "20年代", "range": [2020, 2029]},
            ],
            "genres": list(GENRE_SIMPLIFIED_TO_TRADITIONAL.values()),  # 繁體中文
            "max_selections": {
                "eras": 3,
                "genres": 3
            }
        },
        "scoring_dimensions": {
            "keywords_coverage": {"weight": "-30/-15/0", "description": "Keywords 覆蓋度"},
            "mood_tags_coverage": {"weight": "-20/-10/0", "description": "Mood Tags 覆蓋度"},
            "feature_buttons": {"weight": "-25/-15/0", "description": "Feature Buttons 明確度"},
            "abstract_words": {"weight": "-20/-5/+10", "description": "抽象詞檢測"},
            "feature_match_score": {"weight": "-15/-10/0", "description": "Feature 匹配分數"},
            "candidate_count": {"weight": "-15/-10/0", "description": "候選數量"}
        },
        "decision_logic": {
            "threshold": 40,
            "above_threshold": "Embedding (語義理解)",
            "below_threshold": "Feature (快速精準)",
            "total_score_range": 125
        }
    }
