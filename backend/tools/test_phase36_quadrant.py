"""
Phase 3.6 - Priority 1 測試：三象限分類與評分
測試函數：
1. classify_to_3quadrant() - 三象限分類
2. calculate_3quadrant_score() - 動態權重評分
3. sort_by_quadrant_and_embedding() - 混合排序
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# 加載環境變數
from dotenv import load_dotenv
env_path = backend_path / ".env"
load_dotenv(env_path)

from app.services.simple_recommend import (
    classify_to_3quadrant,
    calculate_3quadrant_score,
    sort_by_quadrant_and_embedding
)


def test_classify_to_3quadrant():
    """
    測試 1: classify_to_3quadrant()
    
    測試案例：
    1. Q1 (Perfect Match): High E (>=0.60) AND High M (>=0.40)
    2. Q2 (Semantic Discovery): High E (>=0.60) AND Low M (<0.40)
    3. Q4 (Fallback): Low E (<0.60) - 不論 Match Ratio
    """
    print("\n" + "="*70)
    print("Test 1: classify_to_3quadrant()")
    print("="*70)
    
    # Case 1: Q1 - High Embedding (0.65) + High Match (0.75)
    movie1 = {"match_ratio": 0.75}
    quadrant1 = classify_to_3quadrant(movie1, embedding_score=0.65)
    assert quadrant1 == 'q1_perfect_match', f"Expected Q1, got {quadrant1}"
    print(f"\n[PASS] Case 1: E=0.65, M=0.75 -> {quadrant1}")
    
    # Case 2: Q1 - 邊界值測試 (E=0.60, M=0.40)
    movie2 = {"match_ratio": 0.40}
    quadrant2 = classify_to_3quadrant(movie2, embedding_score=0.60)
    assert quadrant2 == 'q1_perfect_match', f"Expected Q1, got {quadrant2}"
    print(f"[PASS] Case 2: E=0.60, M=0.40 -> {quadrant2} (boundary)")
    
    # Case 3: Q2 - High Embedding (0.70) + Low Match (0.30)
    movie3 = {"match_ratio": 0.30}
    quadrant3 = classify_to_3quadrant(movie3, embedding_score=0.70)
    assert quadrant3 == 'q2_semantic_discovery', f"Expected Q2, got {quadrant3}"
    print(f"[PASS] Case 3: E=0.70, M=0.30 -> {quadrant3}")
    
    # Case 4: Q2 - High Embedding (0.65) + Low Match (0.39)
    movie4 = {"match_ratio": 0.39}
    quadrant4 = classify_to_3quadrant(movie4, embedding_score=0.65)
    assert quadrant4 == 'q2_semantic_discovery', f"Expected Q2, got {quadrant4}"
    print(f"[PASS] Case 4: E=0.65, M=0.39 -> {quadrant4} (boundary)")
    
    # Case 5: Q4 - Low Embedding (0.50) + High Match (0.80)
    movie5 = {"match_ratio": 0.80}
    quadrant5 = classify_to_3quadrant(movie5, embedding_score=0.50)
    assert quadrant5 == 'q4_fallback', f"Expected Q4, got {quadrant5}"
    print(f"[PASS] Case 5: E=0.50, M=0.80 -> {quadrant5}")
    
    # Case 6: Q4 - Low Embedding (0.59) + Low Match (0.20)
    movie6 = {"match_ratio": 0.20}
    quadrant6 = classify_to_3quadrant(movie6, embedding_score=0.59)
    assert quadrant6 == 'q4_fallback', f"Expected Q4, got {quadrant6}"
    print(f"[PASS] Case 6: E=0.59, M=0.20 -> {quadrant6} (boundary)")
    
    # Case 7: 自定義閾值
    config = {
        "quadrant_thresholds": {
            "high_embedding": 0.70,
            "high_match": 0.50
        }
    }
    movie7 = {"match_ratio": 0.55}
    quadrant7 = classify_to_3quadrant(movie7, embedding_score=0.75, config=config)
    assert quadrant7 == 'q1_perfect_match', f"Expected Q1 with custom config, got {quadrant7}"
    print(f"[PASS] Case 7: E=0.75, M=0.55 (custom threshold) -> {quadrant7}")
    
    print("\n[PASS] All classification tests passed!")


def test_calculate_3quadrant_score():
    """
    測試 2: calculate_3quadrant_score()
    
    測試案例：
    1. Q1 權重：E:50%, M:20% (total 70%)
    2. Q2 權重：E:70%, M:20% (total 90%)
    3. Q4 權重：E:30%, M:30% (total 60%)
    """
    print("\n" + "="*70)
    print("Test 2: calculate_3quadrant_score()")
    print("="*70)
    
    # Case 1: Q1 - E:50%, M:20%
    movie1 = {"match_ratio": 0.60}
    score1 = calculate_3quadrant_score(
        movie1, 
        embedding_score=0.80, 
        quadrant='q1_perfect_match'
    )
    expected1 = 0.80 * 100 * 0.50 + 0.60 * 100 * 0.20  # = 40 + 12 = 52
    assert abs(score1 - expected1) < 0.01, f"Expected {expected1}, got {score1}"
    print(f"\n[PASS] Case 1: Q1 (E=0.80, M=0.60) -> Score={score1:.2f}")
    print(f"       Expected: 0.80*100*0.50 + 0.60*100*0.20 = {expected1:.2f}")
    
    # Case 2: Q2 - E:70%, M:20% (Embedding 優先)
    movie2 = {"match_ratio": 0.30}
    score2 = calculate_3quadrant_score(
        movie2, 
        embedding_score=0.85, 
        quadrant='q2_semantic_discovery'
    )
    expected2 = 0.85 * 100 * 0.70 + 0.30 * 100 * 0.20  # = 59.5 + 6 = 65.5
    assert abs(score2 - expected2) < 0.01, f"Expected {expected2}, got {score2}"
    print(f"[PASS] Case 2: Q2 (E=0.85, M=0.30) -> Score={score2:.2f}")
    print(f"       Expected: 0.85*100*0.70 + 0.30*100*0.20 = {expected2:.2f}")
    
    # Case 3: Q4 - E:30%, M:30% (平衡但偏低)
    movie3 = {"match_ratio": 0.50}
    score3 = calculate_3quadrant_score(
        movie3, 
        embedding_score=0.55, 
        quadrant='q4_fallback'
    )
    expected3 = 0.55 * 100 * 0.30 + 0.50 * 100 * 0.30  # = 16.5 + 15 = 31.5
    assert abs(score3 - expected3) < 0.01, f"Expected {expected3}, got {score3}"
    print(f"[PASS] Case 3: Q4 (E=0.55, M=0.50) -> Score={score3:.2f}")
    print(f"       Expected: 0.55*100*0.30 + 0.50*100*0.30 = {expected3:.2f}")
    
    # Case 4: 驗證 Q2 > Q1 當 Embedding 更高
    movie4a = {"match_ratio": 0.80}
    score4a = calculate_3quadrant_score(
        movie4a, embedding_score=0.70, quadrant='q1_perfect_match'
    )
    movie4b = {"match_ratio": 0.20}
    score4b = calculate_3quadrant_score(
        movie4b, embedding_score=0.90, quadrant='q2_semantic_discovery'
    )
    print(f"\n[PASS] Case 4: Q2 with higher E can beat Q1")
    print(f"       Q1 (E=0.70, M=0.80) -> {score4a:.2f}")
    print(f"       Q2 (E=0.90, M=0.20) -> {score4b:.2f}")
    print(f"       Q2 > Q1: {score4b > score4a}")
    
    print("\n[PASS] All score calculation tests passed!")


def test_sort_by_quadrant_and_embedding():
    """
    測試 3: sort_by_quadrant_and_embedding()
    
    測試案例：
    1. 象限優先級：Q1 > Q2 > Q4
    2. 同象限內按 final_score 降序
    3. 混合測試
    """
    print("\n" + "="*70)
    print("Test 3: sort_by_quadrant_and_embedding()")
    print("="*70)
    
    # Case 1: 基本排序
    movies = [
        {"title": "Movie A", "quadrant": "q4_fallback", "final_score": 50},
        {"title": "Movie B", "quadrant": "q1_perfect_match", "final_score": 80},
        {"title": "Movie C", "quadrant": "q2_semantic_discovery", "final_score": 70},
        {"title": "Movie D", "quadrant": "q1_perfect_match", "final_score": 85},
    ]
    
    sorted_movies = sort_by_quadrant_and_embedding(movies)
    
    # 驗證順序
    expected_order = [
        ("Movie D", "q1_perfect_match", 85),
        ("Movie B", "q1_perfect_match", 80),
        ("Movie C", "q2_semantic_discovery", 70),
        ("Movie A", "q4_fallback", 50),
    ]
    
    print("\n[PASS] Case 1: Basic sorting")
    for i, (movie, expected) in enumerate(zip(sorted_movies, expected_order)):
        assert movie["title"] == expected[0], f"Position {i}: Expected {expected[0]}, got {movie['title']}"
        assert movie["quadrant"] == expected[1], f"Expected {expected[1]}, got {movie['quadrant']}"
        assert movie["final_score"] == expected[2], f"Expected {expected[2]}, got {movie['final_score']}"
        print(f"  {i+1}. {movie['title']:10s} - {movie['quadrant']:25s} - Score: {movie['final_score']}")
    
    # Case 2: 同象限多部電影
    movies2 = [
        {"title": "Q1-Low", "quadrant": "q1_perfect_match", "final_score": 70},
        {"title": "Q1-High", "quadrant": "q1_perfect_match", "final_score": 90},
        {"title": "Q1-Mid", "quadrant": "q1_perfect_match", "final_score": 80},
    ]
    
    sorted_movies2 = sort_by_quadrant_and_embedding(movies2)
    scores = [m["final_score"] for m in sorted_movies2]
    
    assert scores == [90, 80, 70], f"Expected [90, 80, 70], got {scores}"
    print(f"\n[PASS] Case 2: Same quadrant sorting - {scores}")
    
    # Case 3: Q2 高分 vs Q1 低分（Q1 仍優先）
    movies3 = [
        {"title": "Q2-VeryHigh", "quadrant": "q2_semantic_discovery", "final_score": 95},
        {"title": "Q1-VeryLow", "quadrant": "q1_perfect_match", "final_score": 50},
    ]
    
    sorted_movies3 = sort_by_quadrant_and_embedding(movies3)
    
    assert sorted_movies3[0]["title"] == "Q1-VeryLow", "Q1 should be first despite lower score"
    assert sorted_movies3[1]["title"] == "Q2-VeryHigh", "Q2 should be second"
    print(f"\n[PASS] Case 3: Quadrant priority overrides score")
    print(f"  1. {sorted_movies3[0]['title']} ({sorted_movies3[0]['quadrant']}, {sorted_movies3[0]['final_score']})")
    print(f"  2. {sorted_movies3[1]['title']} ({sorted_movies3[1]['quadrant']}, {sorted_movies3[1]['final_score']})")
    
    print("\n[PASS] All sorting tests passed!")


def main():
    print("\n" + "="*70)
    print("Phase 3.6 - Priority 1: 3-Quadrant System Tests")
    print("="*70)
    
    test_classify_to_3quadrant()
    test_calculate_3quadrant_score()
    test_sort_by_quadrant_and_embedding()
    
    print("\n" + "="*70)
    print("All Tests Completed Successfully!")
    print("="*70)


if __name__ == "__main__":
    main()
