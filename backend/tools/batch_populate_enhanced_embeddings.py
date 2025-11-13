"""
Batch populate enhanced embeddings for all movies in the database.

This script:
1. Fetches all movies from the database
2. Generates enhanced embedding text (title + genres + keywords + mood_tags + overview)
3. Calls OpenAI Embedding API to get vectors
4. Stores results in movie_vectors table

Estimated cost: ~$0.004 for 675 movies (300 tokens avg @ $0.00002/1K tokens)
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
from typing import Dict, List, Any
from sqlalchemy import text
from db.database import SessionLocal
from app.services.embedding_service import get_embedding, EMBEDDING_MODEL

# Configuration
BATCH_SIZE = 50  # Process 50 movies at a time
DELAY_BETWEEN_BATCHES = 1  # 1 second delay to avoid rate limits


def generate_enhanced_embedding_text(movie: Dict[str, Any]) -> str:
    """
    Generate enhanced text for embedding that includes all features.
    
    Format:
    Title: {title} | Genres: {genres} | Mood: {mood_tags} | Keywords: {keywords} | Overview: {overview}
    """
    parts = []
    
    # 1. Title (always included)
    if movie.get('title'):
        parts.append(f"Title: {movie['title']}")
    
    # 2. Genres (JSONB array)
    if movie.get('genres'):
        genres_list = movie['genres'] if isinstance(movie['genres'], list) else []
        if genres_list:
            genres_str = ", ".join(genres_list)
            parts.append(f"Genres: {genres_str}")
    
    # 3. Mood Tags (JSONB array)
    if movie.get('mood_tags'):
        mood_tags_list = movie['mood_tags'] if isinstance(movie['mood_tags'], list) else []
        if mood_tags_list:
            # Limit to top 10 mood tags to avoid too long text
            mood_str = ", ".join(mood_tags_list[:10])
            parts.append(f"Mood: {mood_str}")
    
    # 4. Keywords (JSONB array)
    if movie.get('keywords'):
        keywords_list = movie['keywords'] if isinstance(movie['keywords'], list) else []
        if keywords_list:
            # Limit to top 10 keywords
            keywords_str = ", ".join(keywords_list[:10])
            parts.append(f"Keywords: {keywords_str}")
    
    # 5. Overview (text)
    if movie.get('overview'):
        parts.append(f"Overview: {movie['overview']}")
    
    return " | ".join(parts)


def fetch_all_movies(db_session) -> List[Dict[str, Any]]:
    """Fetch all movies with their metadata."""
    query = text("""
        SELECT 
            tmdb_id,
            title,
            overview,
            genres,
            keywords,
            mood_tags
        FROM movies
        ORDER BY tmdb_id
    """)
    
    result = db_session.execute(query)
    
    movies = []
    for row in result:
        movies.append({
            'tmdb_id': row[0],
            'title': row[1],
            'overview': row[2],
            'genres': row[3],
            'keywords': row[4],
            'mood_tags': row[5]
        })
    
    return movies


def batch_populate_embeddings():
    """Main function to populate embeddings."""
    print("=" * 80)
    print("Enhanced Movie Embeddings - Batch Population Script")
    print("=" * 80)
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Embedding Dimension: 1536")
    print(f"Batch Size: {BATCH_SIZE}")
    print()
    
    db_session = SessionLocal()
    
    try:
        # 1. Fetch all movies
        print("[1/4] Fetching all movies from database...")
        movies = fetch_all_movies(db_session)
        print(f"✓ Found {len(movies)} movies")
        print()
        
        # 2. Check existing embeddings
        print("[2/4] Checking existing embeddings...")
        existing_query = text("SELECT COUNT(*) FROM movie_vectors")
        existing_count = db_session.execute(existing_query).scalar()
        print(f"✓ Found {existing_count} existing embeddings")
        
        if existing_count > 0:
            response = input(f"Delete {existing_count} existing embeddings and regenerate? (yes/no): ")
            if response.lower() == 'yes':
                delete_query = text("DELETE FROM movie_vectors")
                db_session.execute(delete_query)
                db_session.commit()
                print("✓ Deleted existing embeddings")
            else:
                print("✗ Skipping movies with existing embeddings")
        print()
        
        # 3. Generate embeddings in batches
        print(f"[3/4] Generating embeddings (batch size: {BATCH_SIZE})...")
        
        total_movies = len(movies)
        successful = 0
        failed = 0
        skipped = 0
        total_tokens = 0
        
        for i in range(0, total_movies, BATCH_SIZE):
            batch = movies[i:i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (total_movies + BATCH_SIZE - 1) // BATCH_SIZE
            
            print(f"\n  Batch {batch_num}/{total_batches} (movies {i+1}-{min(i+BATCH_SIZE, total_movies)}):")
            
            for movie in batch:
                tmdb_id = movie['tmdb_id']
                title = movie['title']
                
                try:
                    # Check if embedding already exists (if we're not deleting)
                    if existing_count > 0:
                        check_query = text("SELECT 1 FROM movie_vectors WHERE tmdb_id = :tmdb_id")
                        exists = db_session.execute(check_query, {"tmdb_id": tmdb_id}).fetchone()
                        if exists:
                            skipped += 1
                            continue
                    
                    # Generate enhanced text
                    embedding_text = generate_enhanced_embedding_text(movie)
                    
                    # Estimate tokens (rough: 1 token ≈ 4 chars)
                    estimated_tokens = len(embedding_text) // 4
                    total_tokens += estimated_tokens
                    
                    # Get embedding from OpenAI
                    embedding_vector = get_embedding(embedding_text)
                    
                    # Store in database
                    insert_query = text("""
                        INSERT INTO movie_vectors (tmdb_id, embedding_text, embedding, embedding_version, updated_at)
                        VALUES (:tmdb_id, :embedding_text, :embedding, :embedding_version, now())
                        ON CONFLICT (tmdb_id) 
                        DO UPDATE SET 
                            embedding_text = EXCLUDED.embedding_text,
                            embedding = EXCLUDED.embedding,
                            embedding_version = EXCLUDED.embedding_version,
                            updated_at = now()
                    """)
                    
                    db_session.execute(insert_query, {
                        "tmdb_id": tmdb_id,
                        "embedding_text": embedding_text,
                        "embedding": json.dumps(embedding_vector),
                        "embedding_version": EMBEDDING_MODEL
                    })
                    db_session.commit()
                    
                    successful += 1
                    print(f"    ✓ {tmdb_id}: {title[:50]}... ({estimated_tokens} tokens)")
                    
                except Exception as e:
                    failed += 1
                    print(f"    ✗ {tmdb_id}: {title[:50]}... - Error: {str(e)}")
                    db_session.rollback()
            
            # Delay between batches to avoid rate limits
            if i + BATCH_SIZE < total_movies:
                print(f"  Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
                time.sleep(DELAY_BETWEEN_BATCHES)
        
        print()
        
        # 4. Summary
        print("[4/4] Summary:")
        print(f"  ✓ Successful: {successful}")
        print(f"  ⊘ Skipped: {skipped}")
        print(f"  ✗ Failed: {failed}")
        print(f"  📊 Total Tokens: ~{total_tokens:,}")
        
        # Cost estimation
        cost_per_1k_tokens = 0.00002
        estimated_cost = (total_tokens / 1000) * cost_per_1k_tokens
        print(f"  💰 Estimated Cost: ${estimated_cost:.4f}")
        
        print()
        print("=" * 80)
        print("✓ Batch population completed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error during batch population: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db_session.close()


if __name__ == "__main__":
    batch_populate_embeddings()
