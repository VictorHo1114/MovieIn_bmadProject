"""
Fill missing keywords, mood_tags, and embeddings for incomplete movies.

This script processes the 361 movies missing feature data in three phases:
Phase 1: Fetch keywords from TMDB API
Phase 2: Generate mood_tags via GPT-4
Phase 3: Generate embeddings via OpenAI API and migrate to pgvector

Usage: python tools/fill_missing_data.py
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
import requests
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from db.database import SessionLocal
from app.services.embedding_service import get_embedding
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BATCH_SIZE = 20
DELAY_BETWEEN_BATCHES = 2
DELAY_BETWEEN_API_CALLS = 0.5

client = OpenAI(api_key=OPENAI_API_KEY)

# ===== PHASE 1: FETCH KEYWORDS FROM TMDB =====

def fetch_keywords_from_tmdb(tmdb_id: int, max_retries=3) -> List[str]:
    """Fetch keywords from TMDB API with retry logic."""
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/keywords?api_key={TMDB_API_KEY}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                keywords = [kw["name"] for kw in data.get("keywords", [])[:10]]  # Top 10
                return keywords
            elif response.status_code == 404:
                print(f"  ⚠️  TMDB ID {tmdb_id} not found")
                return []
            else:
                print(f"  ⚠️  Attempt {attempt+1}/{max_retries} failed: {response.status_code}")
                time.sleep(1)
        except Exception as e:
            print(f"  ⚠️  Attempt {attempt+1}/{max_retries} error: {e}")
            time.sleep(1)
    
    return []

# ===== PHASE 2: GENERATE MOOD_TAGS VIA GPT-4 =====

def analyze_mood_tags(title: str, overview: str, genres: List[str], keywords: List[str], max_retries=3) -> List[str]:
    """Generate mood_tags using GPT-4 with retry logic."""
    genres_str = ", ".join(genres) if genres else "Unknown"
    keywords_str = ", ".join(keywords[:5]) if keywords else "None"
    overview_snippet = overview[:200] if overview else "No description"
    
    prompt = f"""Based on this movie information, select 2-3 mood tags from this list:
[溫馨感人, 緊張刺激, 輕鬆搞笑, 浪漫甜蜜, 驚悚恐怖, 史詩壯闊, 深沉哲理, 勵志正能量, 懸疑燒腦, 黑暗沉重, 奇幻冒險, 懷舊復古, 都市時尚, 熱血動作, 溫情療癒]

Movie: {title}
Genres: {genres_str}
Keywords: {keywords_str}
Overview: {overview_snippet}

Return ONLY a JSON array like ["tag1", "tag2"], no explanation."""
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=50
            )
            result = response.choices[0].message.content.strip()
            mood_tags = json.loads(result)
            return mood_tags if isinstance(mood_tags, list) else []
        except Exception as e:
            print(f"  ⚠️  GPT-4 attempt {attempt+1}/{max_retries} error: {e}")
            time.sleep(2)
    
    return []

# ===== PHASE 3: GENERATE EMBEDDINGS + PGVECTOR =====

def generate_enhanced_embedding_text(movie: Dict[str, Any]) -> str:
    """Generate enhanced text for embedding."""
    parts = []
    if movie.get("title"):
        parts.append(f"Title: {movie['title']}")
    if movie.get("genres"):
        parts.append(f"Genres: {', '.join(movie['genres'])}")
    if movie.get("mood_tags"):
        parts.append(f"Mood: {', '.join(movie['mood_tags'])}")
    if movie.get("keywords"):
        parts.append(f"Keywords: {', '.join(movie['keywords'][:5])}")
    if movie.get("overview"):
        parts.append(f"Overview: {movie['overview']}")
    
    return " | ".join(parts)

def generate_embedding(text: str, max_retries=3) -> Optional[List[float]]:
    """Generate embedding via OpenAI API with retry logic."""
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"  ⚠️  Embedding attempt {attempt+1}/{max_retries} error: {e}")
            time.sleep(2)
    
    return None

# ===== MAIN PROCESSING PIPELINE =====

def fill_missing_data():
    """Main function to fill all missing data."""
    db = SessionLocal()
    
    try:
        # Get movies missing keywords/mood_tags/embeddings
        query = text("""
            SELECT m.tmdb_id, m.title, m.overview, m.genres, m.keywords, m.mood_tags
            FROM movies m
            LEFT JOIN movie_vectors mv ON m.tmdb_id = mv.tmdb_id
            WHERE mv.tmdb_id IS NULL OR m.keywords IS NULL OR m.mood_tags IS NULL
            ORDER BY m.tmdb_id
        """)
        
        movies = db.execute(query).mappings().all()
        total = len(movies)
        
        print(f"\n🎬 Found {total} movies needing data enrichment\n")
        print("=" * 60)
        
        success_count = 0
        fail_count = 0
        
        for idx, movie in enumerate(movies, 1):
            tmdb_id = movie["tmdb_id"]
            title = movie["title"]
            
            print(f"\n[{idx}/{total}] Processing: {title} (ID: {tmdb_id})")
            
            try:
                # Convert JSONB to Python lists
                genres = movie["genres"] if movie["genres"] else []
                keywords = movie["keywords"] if movie["keywords"] else []
                mood_tags = movie["mood_tags"] if movie["mood_tags"] else []
                overview = movie["overview"] or ""
                
                # Phase 1: Fetch keywords if missing
                if not keywords:
                    print("  📋 Fetching keywords from TMDB...")
                    keywords = fetch_keywords_from_tmdb(tmdb_id)
                    if keywords:
                        db.execute(
                            text("UPDATE movies SET keywords = :kw WHERE tmdb_id = :id"),
                            {"kw": json.dumps(keywords), "id": tmdb_id}
                        )
                        db.commit()
                        print(f"  ✅ Keywords: {keywords[:3]}...")
                    time.sleep(DELAY_BETWEEN_API_CALLS)
                
                # Phase 2: Generate mood_tags if missing
                if not mood_tags:
                    print("  🎭 Generating mood_tags via GPT-4...")
                    mood_tags = analyze_mood_tags(title, overview, genres, keywords)
                    if mood_tags:
                        db.execute(
                            text("UPDATE movies SET mood_tags = :mt WHERE tmdb_id = :id"),
                            {"mt": json.dumps(mood_tags), "id": tmdb_id}
                        )
                        db.commit()
                        print(f"  ✅ Mood Tags: {mood_tags}")
                    time.sleep(DELAY_BETWEEN_API_CALLS)
                
                # Phase 3: Generate embedding + pgvector
                check_embedding = db.execute(
                    text("SELECT 1 FROM movie_vectors WHERE tmdb_id = :id"),
                    {"id": tmdb_id}
                ).fetchone()
                
                if not check_embedding:
                    print("  🧠 Generating embedding...")
                    enhanced_text = generate_enhanced_embedding_text({
                        "title": title,
                        "genres": genres,
                        "keywords": keywords,
                        "mood_tags": mood_tags,
                        "overview": overview
                    })
                    
                    embedding = generate_embedding(enhanced_text)
                    
                    if embedding:
                        # Store in both JSONB and pgvector formats
                        db.execute(
                            text("""
                                INSERT INTO movie_vectors (tmdb_id, embedding, embedding_vector)
                                VALUES (:id, :emb_json, CAST(:emb_vec AS vector(1536)))
                            """),
                            {
                                "id": tmdb_id,
                                "emb_json": json.dumps(embedding),
                                "emb_vec": str(embedding)
                            }
                        )
                        db.commit()
                        print("  ✅ Embedding stored in JSONB + pgvector")
                    
                    time.sleep(DELAY_BETWEEN_API_CALLS)
                
                success_count += 1
                print(f"  🎉 Successfully processed {title}")
                
            except Exception as e:
                fail_count += 1
                print(f"  ❌ Failed to process {title}: {e}")
                db.rollback()
                continue
            
            # Batch delay
            if idx % BATCH_SIZE == 0:
                print(f"\n⏸️  Batch {idx//BATCH_SIZE} complete, waiting {DELAY_BETWEEN_BATCHES}s...\n")
                time.sleep(DELAY_BETWEEN_BATCHES)
        
        # Final summary
        print("\n" + "=" * 60)
        print(f"\n🏁 Processing Complete!")
        print(f"  ✅ Success: {success_count}/{total}")
        print(f"  ❌ Failed: {fail_count}/{total}")
        
    finally:
        db.close()

if __name__ == "__main__":
    fill_missing_data()
