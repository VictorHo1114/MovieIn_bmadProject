# app/services/embedding_service.py
"""
向量語義搜尋服務
使用 OpenAI Embeddings 進行電影推薦的語義相似度計算
"""
import os
import json
import random
import numpy as np
from typing import List, Dict, Any, Optional
from openai import OpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# OpenAI 客戶端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 使用 text-embedding-3-small（便宜且效果好）
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def get_embedding(text: str) -> List[float]:
    """
    獲取文本的 embedding 向量
    
    成本：~$0.00002 per 1K tokens
    """
    if not text or not text.strip():
        # 空文本返回零向量
        return [0.0] * EMBEDDING_DIM
    
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    計算兩個向量的 cosine similarity
    
    返回值範圍：[-1, 1]，越接近 1 表示越相似
    """
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    
    return float(dot_product / (norm_v1 * norm_v2))


def store_movie_embedding(
    db_session: Session,
    tmdb_id: int,
    overview: str
) -> None:
    """
    計算並儲存電影的 embedding
    """
    try:
        embedding = get_embedding(overview)
        embedding_json = json.dumps(embedding)
        
        # 使用 UPSERT (PostgreSQL)
        query = text("""
            INSERT INTO movie_vectors (tmdb_id, embedding, overview, updated_at)
            VALUES (:tmdb_id, :embedding, :overview, now())
            ON CONFLICT (tmdb_id) 
            DO UPDATE SET 
                embedding = EXCLUDED.embedding,
                overview = EXCLUDED.overview,
                updated_at = now()
        """)
        
        db_session.execute(query, {
            "tmdb_id": tmdb_id,
            "embedding": embedding_json,
            "overview": overview
        })
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e


async def get_stored_embeddings(
    db_session: Session,
    tmdb_ids: List[int]
) -> Dict[int, List[float]]:
    """
    批次取得已儲存的 embeddings
    
    返回：{tmdb_id: embedding_vector}
    """
    if not tmdb_ids:
        return {}
    
    query = text("""
        SELECT tmdb_id, embedding
        FROM movie_vectors
        WHERE tmdb_id = ANY(:ids)
    """)
    
    result = db_session.execute(query, {"ids": tmdb_ids})
    
    embeddings = {}
    for row in result:
        tmdb_id = row[0]
        embedding_json = row[1]
        embeddings[tmdb_id] = json.loads(embedding_json)
    
    return embeddings


def calculate_diversity_score(
    movies: List[Dict[str, Any]],
    selected_movies: List[Dict[str, Any]]
) -> Dict[int, float]:
    """
    計算多樣性分數，降低與已選電影相似的電影權重
    
    參數：
        movies: 候選電影列表
        selected_movies: 已選擇的電影列表
    
    返回：
        {tmdb_id: diversity_score}，範圍 [0, 1]
    """
    if not selected_movies:
        # 沒有已選電影時，所有電影的多樣性分數都是 1.0
        return {movie["id"]: 1.0 for movie in movies}
    
    diversity_scores = {}
    
    for movie in movies:
        # 計算與已選電影的「差異度」
        genre_ids = set(movie.get("genre_ids", []))
        release_year = movie.get("release_date", "")[:4] if movie.get("release_date") else None
        
        penalties = []
        for selected in selected_movies:
            # 類型重疊懲罰
            selected_genres = set(selected.get("genre_ids", []))
            genre_overlap = len(genre_ids & selected_genres) / max(len(genre_ids | selected_genres), 1)
            
            # 年份接近懲罰
            selected_year = selected.get("release_date", "")[:4] if selected.get("release_date") else None
            year_penalty = 0.0
            if release_year and selected_year:
                try:
                    year_diff = abs(int(release_year) - int(selected_year))
                    year_penalty = max(0, 1 - year_diff / 10)  # 10年內有懲罰
                except:
                    pass
            
            # 總懲罰 = 類型重疊 * 0.7 + 年份接近 * 0.3
            penalty = genre_overlap * 0.7 + year_penalty * 0.3
            penalties.append(penalty)
        
        # 多樣性分數 = 1 - 平均懲罰
        avg_penalty = sum(penalties) / len(penalties)
        diversity_scores[movie["id"]] = max(0.2, 1 - avg_penalty)  # 最低 0.2，避免完全排除
    
    return diversity_scores


async def rerank_by_semantic_similarity(
    query_text: str,
    candidate_movies: List[Dict[str, Any]],
    db_session: Session,
    top_k: int = 10,
    diversity_weight: float = 0.3,  # 多樣性權重
    boost_exact_matches: bool = False,  # 是否提升精確匹配權重
    boost_keyword_matches: bool = False,  # 新增：是否提升 keyword 匹配權重
    randomness: float = 0.3  # 隨機性參數（0.0 完全確定，1.0 完全隨機）
) -> List[Dict[str, Any]]:
    """
    使用語義相似度對候選電影進行重新排序，並加入多樣性機制
    
    參數：
        query_text: 用戶查詢文本
        candidate_movies: 候選電影列表（來自 TMDB）
        db_session: 資料庫 session
        top_k: 返回前 K 部電影
        diversity_weight: 多樣性權重（0.0 = 純相似度，1.0 = 純多樣性）
        boost_exact_matches: 是否提升精確匹配權重
        boost_keyword_matches: 是否提升 keyword 匹配權重
        randomness: 隨機性參數（0.0 完全確定，1.0 完全隨機）
    
    返回：
        排序後的電影列表（包含 similarity_score）
    """
    if not candidate_movies:
        return []
    
    # 1. 計算用戶查詢的 embedding
    print(f"[Embedding] 計算查詢 embedding: '{query_text[:50]}...'")
    query_embedding = get_embedding(query_text)
    
    # 2. 取得候選電影的 embeddings
    tmdb_ids = [movie["id"] for movie in candidate_movies]
    stored_embeddings = await get_stored_embeddings(db_session, tmdb_ids)
    
    print(f"[Embedding] 找到 {len(stored_embeddings)} / {len(candidate_movies)} 部電影的 embeddings")
    
    # 3. 對於沒有 embedding 的電影，即時計算並儲存
    movies_needing_embedding = [
        movie for movie in candidate_movies 
        if movie["id"] not in stored_embeddings
    ]
    
    if movies_needing_embedding:
        print(f"[Embedding] 即時計算 {len(movies_needing_embedding)} 部電影的 embeddings")
        for movie in movies_needing_embedding:
            overview = movie.get("overview", "")
            if overview:
                try:
                    store_movie_embedding(db_session, movie["id"], overview)
                    # 重新取得
                    stored_embeddings[movie["id"]] = get_embedding(overview)
                except Exception as e:
                    print(f"[Embedding] 計算失敗 (tmdb_id={movie['id']}): {e}")
    
    # 4. 計算相似度分數
    for movie in candidate_movies:
        tmdb_id = movie["id"]
        if tmdb_id in stored_embeddings:
            similarity = cosine_similarity(query_embedding, stored_embeddings[tmdb_id])
            
            # [新增] 根據 randomness 參數添加可控的隨機擾動
            # randomness=0.0 → 無擾動
            # randomness=0.3 → ±3% 擾動
            # randomness=1.0 → ±10% 擾動
            noise_range = randomness * 0.1
            noise = random.uniform(-noise_range, noise_range)
            base_score = max(0, min(1, similarity + noise))
            
            # [新增] 如果是精確匹配，提升權重
            if boost_exact_matches and movie.get("is_exact_match"):
                base_score = min(1.0, base_score * 1.5)  # 提升 50%
                print(f"[Embedding] 精確匹配加權: {movie.get('title')} - {base_score:.3f}")
            
            # [新增] 如果有 keyword 匹配，提升權重
            if boost_keyword_matches and movie.get("has_keyword_match"):
                base_score = min(1.0, base_score * 1.3)  # 提升 30%
                print(f"[Embedding] Keyword 匹配加權: {movie.get('title')} - {base_score:.3f}")
            
            movie["similarity_score"] = base_score
        else:
            movie["similarity_score"] = 0.0
    
    # 5. 使用 Maximal Marginal Relevance (MMR) 選擇多樣化結果
    selected_movies = []
    remaining_movies = candidate_movies.copy()
    
    while len(selected_movies) < top_k and remaining_movies:
        # 計算當前候選電影的多樣性分數
        diversity_scores = calculate_diversity_score(remaining_movies, selected_movies)
        
        # 計算綜合分數 = 相似度 * (1 - diversity_weight) + 多樣性 * diversity_weight
        for movie in remaining_movies:
            similarity = movie["similarity_score"]
            diversity = diversity_scores.get(movie["id"], 1.0)
            movie["final_score"] = similarity * (1 - diversity_weight) + diversity * diversity_weight
        
        # 選擇分數最高的電影
        remaining_movies.sort(key=lambda x: x["final_score"], reverse=True)
        best_movie = remaining_movies.pop(0)
        selected_movies.append(best_movie)
    
    print(f"[Embedding] 返回 {len(selected_movies)} 部電影，Top 10 分數:")
    for i, movie in enumerate(selected_movies[:10]):
        print(f"  {i+1}. {movie.get('title', 'Unknown')} - 相似度:{movie['similarity_score']:.3f}, 最終分數:{movie.get('final_score', 0):.3f}")
    
    return selected_movies