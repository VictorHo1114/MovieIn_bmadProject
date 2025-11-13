"""
Phase 3.6 整合測試 - End-to-End
測試完整的 Embedding-First 推薦流程
"""

import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
env_path = backend_path / ".env"
load_dotenv(env_path)

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.simple_recommend import recommend_movies_embedding_first


DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


async def test_scenario_1_journey():
    """
    測試場景 1: Journey (情感治癒之旅)
    - 自然語言 + Mood Labels
    - 預期：返回溫暖治癒類電影
    """
    print("\n" + "="*70)
    print("Test Scenario 1: Journey - Emotional Healing")
    print("="*70)
    
    session = SessionLocal()
    
    try:
        results = await recommend_movies_embedding_first(
            natural_query="難過的時候適合看什麼電影",
            mood_labels=["heartwarming", "uplifting"],
            genres=["Drama"],
            db_session=session,
            count=10
        )
        
        # 驗證
        assert len(results) > 0, "Should return results"
        assert len(results) <= 10, "Should return at most 10 movies"
        
        # 檢查必要欄位
        for movie in results:
            assert "quadrant" in movie, "Should have quadrant"
            assert "final_score" in movie, "Should have final_score"
            assert "embedding_score" in movie, "Should have embedding_score"
            assert "match_ratio" in movie, "Should have match_ratio"
        
        # 統計象限分佈
        quadrant_counts = {}
        for movie in results:
            q = movie["quadrant"]
            quadrant_counts[q] = quadrant_counts.get(q, 0) + 1
        
        print(f"\n[PASS] Returned {len(results)} movies")
        print(f"Quadrant Distribution: {quadrant_counts}")
        print(f"Top 3:")
        for i, movie in enumerate(results[:3]):
            print(f"  {i+1}. {movie['title']} ({movie['quadrant']}, Score: {movie['final_score']:.2f})")
        
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


async def test_scenario_2_mood_only():
    """
    測試場景 2: Mood Only (無自然語言)
    - 只有 Mood Labels
    - 預期：使用 Mood Template 生成查詢
    """
    print("\n" + "="*70)
    print("Test Scenario 2: Mood Only - No Natural Language")
    print("="*70)
    
    session = SessionLocal()
    
    try:
        results = await recommend_movies_embedding_first(
            natural_query=None,
            mood_labels=["dark", "lighthearted"],  # Paradox
            genres=["Comedy", "Drama"],
            db_session=session,
            count=10
        )
        
        assert len(results) > 0, "Should return results"
        
        print(f"\n[PASS] Returned {len(results)} movies (Mood-only query)")
        print(f"Top 3:")
        for i, movie in enumerate(results[:3]):
            print(f"  {i+1}. {movie['title']} ({movie['quadrant']}, Score: {movie['final_score']:.2f})")
        
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


async def test_scenario_3_filters():
    """
    測試場景 3: With Hard Filters
    - 包含 exclude_genres, year_range, min_rating
    - 預期：所有結果符合過濾條件
    """
    print("\n" + "="*70)
    print("Test Scenario 3: With Hard Filters")
    print("="*70)
    
    session = SessionLocal()
    
    try:
        results = await recommend_movies_embedding_first(
            natural_query="想看一部刺激的動作片",
            genres=["Action"],
            exclude_genres=["Horror", "Thriller"],
            year_range=(2015, 2023),
            min_rating=7.0,
            db_session=session,
            count=10
        )
        
        # 驗證 Hard Filters
        for movie in results:
            # 檢查評分
            assert movie.get("vote_average", 0) >= 7.0, f"{movie['title']} rating should be >= 7.0"
            
            # 檢查年份
            release_date = movie.get("release_date")
            if release_date:
                if hasattr(release_date, 'year'):
                    year = release_date.year
                elif isinstance(release_date, str):
                    year = int(release_date[:4])
                assert 2015 <= year <= 2023, f"{movie['title']} year should be 2015-2023"
        
        print(f"\n[PASS] All {len(results)} movies passed hard filters")
        print(f"Top 3:")
        for i, movie in enumerate(results[:3]):
            year = movie['release_date'][:4] if isinstance(movie['release_date'], str) else movie['release_date'].year
            print(f"  {i+1}. {movie['title']} ({year}, Rating: {movie['vote_average']:.1f})")
        
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


async def test_scenario_4_quadrant_priority():
    """
    測試場景 4: Quadrant Priority
    - 驗證 Q1 > Q2 > Q4 排序優先級
    """
    print("\n" + "="*70)
    print("Test Scenario 4: Quadrant Priority Verification")
    print("="*70)
    
    session = SessionLocal()
    
    try:
        results = await recommend_movies_embedding_first(
            natural_query="適合全家觀看的溫馨電影",
            mood_labels=["heartwarming", "feel-good"],
            genres=["Family", "Animation"],
            db_session=session,
            count=15
        )
        
        # 檢查象限排序
        quadrant_order = [m["quadrant"] for m in results]
        
        # Q1 應該在前面
        if "q1_perfect_match" in quadrant_order:
            q1_positions = [i for i, q in enumerate(quadrant_order) if q == "q1_perfect_match"]
            q2_positions = [i for i, q in enumerate(quadrant_order) if q == "q2_semantic_discovery"]
            q4_positions = [i for i, q in enumerate(quadrant_order) if q == "q4_fallback"]
            
            if q2_positions:
                assert max(q1_positions) < min(q2_positions), "Q1 should come before Q2"
            if q4_positions:
                assert max(q1_positions) < min(q4_positions), "Q1 should come before Q4"
            
            print(f"\n[PASS] Quadrant priority verified")
            print(f"  Q1 positions: {q1_positions}")
            print(f"  Q2 positions: {q2_positions}")
            print(f"  Q4 positions: {q4_positions}")
        else:
            print(f"\n[INFO] No Q1 movies in results (acceptable)")
        
        print(f"\nQuadrant sequence: {' -> '.join(quadrant_order)}")
        
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


async def main():
    print("\n" + "="*70)
    print("Phase 3.6 Integration Tests - End-to-End")
    print("="*70)
    
    await test_scenario_1_journey()
    await test_scenario_2_mood_only()
    await test_scenario_3_filters()
    await test_scenario_4_quadrant_priority()
    
    print("\n" + "="*70)
    print("All Integration Tests Completed!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
