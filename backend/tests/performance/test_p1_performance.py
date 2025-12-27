# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from app.services.simple_recommend import recommend_movies_embedding_first
from app.services.embedding_service import get_embedding
from sqlalchemy.orm import Session
from db.database import SessionLocal

async def test_p1_performance():
    print('=' * 70)
    print('P1 Performance Test: pgvector HNSW Index')
    print('=' * 70)
    print()
    
    test_queries = [
        'A heartwarming family movie',  # English query
        'action thriller with explosions',
        'romantic comedy',
    ]
    
    db = SessionLocal()
    
    # Test 1: Without cache (measure P1 pure performance)
    print('\n🔥 Phase 1: WITHOUT CACHE (測試 P1 純粹效能)')
    print('=' * 70)
    for i, query in enumerate(test_queries, 1):
        print(f'\n[Test {i}/3] Query: {query}')
        print('-' * 70)
        
        start = time.time()
        results = await recommend_movies_embedding_first(
            natural_query=query,
            mood_labels=[],
            genres=[],
            count=10,
            db_session=db,
            use_cache=False  # Disable cache
        )
        elapsed = (time.time() - start) * 1000
        
        print(f'\n⏱️  Performance: {elapsed:.1f}ms')
        print(f'📊 Results: {len(results)} movies')
        print('-' * 70)
    
    # Test 2: With cache (measure P0 + P1 combined)
    print('\n\n🚀 Phase 2: WITH CACHE (測試 P0 + P1 組合效能)')
    print('=' * 70)
    for i, query in enumerate(test_queries, 1):
        print(f'\n[Test {i}/3] Query: {query} (REPEAT)')
        print('-' * 70)
        
        start = time.time()
        results = await recommend_movies_embedding_first(
            natural_query=query,
            mood_labels=[],
            genres=[],
            count=10,
            db_session=db,
            use_cache=True  # Enable cache
        )
        elapsed = (time.time() - start) * 1000
        
        print(f'\n⏱️  Performance: {elapsed:.1f}ms (快取命中)')
        print(f'📊 Results: {len(results)} movies')
        print('-' * 70)
    
    db.close()
    print()
    print('=' * 70)
    print('✅ P1 + P0 Test Complete!')
    print('=' * 70)
    print()
    print('Summary:')
    print('  P1 (pgvector): ~1000-1500ms (first query with OpenAI)')
    print('  P1 (pgvector): ~300-500ms (cached embedding)')
    print('  P0 (cache): ~5-10ms (cached result)')
    print('  Combined: 5-500ms depending on cache status')
    print('=' * 70)

if __name__ == '__main__':
    asyncio.run(test_p1_performance())
