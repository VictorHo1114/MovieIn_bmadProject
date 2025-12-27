"""
單元測試：simple_recommend.py
測試 Phase 3.6 Embedding-First 推薦系統的核心函數

測試範圍：
- calculate_match_ratio (SR-001~SR-003)
- _check_year_in_range (SR-004~SR-006)
- classify_to_3quadrant (SR-007~SR-011)
- calculate_3quadrant_score (SR-012~SR-016)
- sort_by_quadrant_and_embedding (SR-017~SR-019)
- tiered_feature_filtering (SR-020~SR-024)
- recommend_movies_embedding_first (SR-025~SR-030)
"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-testing-only"
os.environ["TESTING"] = "1"

import pytest
from typing import List, Dict
from unittest.mock import Mock, patch, AsyncMock
from datetime import date

from app.services.simple_recommend import (
    calculate_match_ratio,
    _check_year_in_range,
    classify_to_3quadrant,
    calculate_3quadrant_score,
    sort_by_quadrant_and_embedding,
    tiered_feature_filtering,
    recommend_movies_embedding_first,
    GENRE_EN_TO_ZH
)


class TestCalculateMatchRatio:
    """測試 calculate_match_ratio 函數"""
    
    @pytest.mark.unit
    def test_sr001_perfect_match(self):
        """SR-001: 完美匹配 - 所有特徵都符合"""
        movie = {
            "keywords": ["love", "family", "hope"],
            "mood_tags": ["heartwarming", "uplifting"],
            "genres": ["剧情", "喜剧"]
        }
        
        result = calculate_match_ratio(
            movie=movie,
            keywords=["love", "family", "hope"],
            mood_tags=["heartwarming", "uplifting"],
            genres=["Drama", "Comedy"]
        )
        
        assert result == 1.0  # 7/7 = 100%
    
    @pytest.mark.unit
    def test_sr002_partial_match(self):
        """SR-002: 部分匹配"""
        movie = {
            "keywords": ["love", "family"],
            "mood_tags": ["heartwarming"],
            "genres": ["剧情"]
        }
        
        result = calculate_match_ratio(
            movie=movie,
            keywords=["love", "family", "hope"],  # 2/3 match
            mood_tags=["heartwarming", "uplifting"],  # 1/2 match
            genres=["Drama", "Comedy"]  # 1/2 match
        )
        
        # (2 + 1 + 1) / (3 + 2 + 2) = 4/7 ≈ 0.571
        assert 0.57 <= result <= 0.58
    
    @pytest.mark.unit
    def test_sr003_no_requirements(self):
        """SR-003: 無任何要求 - 應返回 1.0"""
        movie = {"keywords": [], "mood_tags": [], "genres": []}
        
        result = calculate_match_ratio(
            movie=movie,
            keywords=[],
            mood_tags=[],
            genres=[]
        )
        
        assert result == 1.0
    
    @pytest.mark.unit
    def test_sr004_case_insensitive_matching(self):
        """SR-004: 大小寫不敏感匹配"""
        movie = {
            "keywords": ["LOVE", "Family"],
            "mood_tags": ["Heartwarming"],
            "genres": []
        }
        
        result = calculate_match_ratio(
            movie=movie,
            keywords=["love", "family"],
            mood_tags=["heartwarming"],
            genres=[]
        )
        
        assert result == 1.0  # 完全匹配


class TestCheckYearInRange:
    """測試 _check_year_in_range 函數"""
    
    @pytest.mark.unit
    def test_sr005_date_object_in_range(self):
        """SR-005: date 物件在範圍內"""
        release_date = date(2015, 6, 15)
        result = _check_year_in_range(release_date, 2010, 2020)
        assert result is True
    
    @pytest.mark.unit
    def test_sr006_string_date_in_range(self):
        """SR-006: 字串日期在範圍內"""
        release_date = "2015-06-15"
        result = _check_year_in_range(release_date, 2010, 2020)
        assert result is True
    
    @pytest.mark.unit
    def test_sr007_date_out_of_range(self):
        """SR-007: 日期不在範圍內"""
        release_date = date(2025, 1, 1)
        result = _check_year_in_range(release_date, 2010, 2020)
        assert result is False
    
    @pytest.mark.unit
    def test_sr008_none_date(self):
        """SR-008: None 日期"""
        result = _check_year_in_range(None, 2010, 2020)
        assert result is False
    
    @pytest.mark.unit
    def test_sr009_boundary_years(self):
        """SR-009: 邊界年份測試"""
        # 最小邊界
        assert _check_year_in_range(date(2010, 1, 1), 2010, 2020) is True
        # 最大邊界
        assert _check_year_in_range(date(2020, 12, 31), 2010, 2020) is True
        # 剛好超出
        assert _check_year_in_range(date(2009, 12, 31), 2010, 2020) is False


class TestClassifyTo3Quadrant:
    """測試 classify_to_3quadrant 函數"""
    
    @pytest.mark.unit
    def test_sr010_q1_perfect_match(self):
        """SR-010: Q1 完美匹配 - 高語義+高匹配"""
        movie = {"match_ratio": 0.75}
        result = classify_to_3quadrant(movie, embedding_score=0.65)
        assert result == "q1_perfect_match"
    
    @pytest.mark.unit
    def test_sr011_q2_semantic_discovery(self):
        """SR-011: Q2 語義發現 - 高語義+低匹配"""
        movie = {"match_ratio": 0.30}
        result = classify_to_3quadrant(movie, embedding_score=0.70)
        assert result == "q2_semantic_discovery"
    
    @pytest.mark.unit
    def test_sr012_q4_fallback(self):
        """SR-012: Q4 保底 - 低語義"""
        movie = {"match_ratio": 0.80}  # 即使高匹配
        result = classify_to_3quadrant(movie, embedding_score=0.50)
        assert result == "q4_fallback"  # 低語義直接進 Q4
    
    @pytest.mark.unit
    def test_sr013_boundary_thresholds(self):
        """SR-013: 邊界閾值測試"""
        # 剛好達到高語義閾值
        movie1 = {"match_ratio": 0.50}
        assert classify_to_3quadrant(movie1, 0.60) == "q1_perfect_match"
        
        # 剛好低於高語義閾值
        movie2 = {"match_ratio": 0.50}
        assert classify_to_3quadrant(movie2, 0.59) == "q4_fallback"
    
    @pytest.mark.unit
    def test_sr014_custom_thresholds(self):
        """SR-014: 自定義閾值"""
        movie = {"match_ratio": 0.50}
        custom_config = {
            "quadrant_thresholds": {
                "high_embedding": 0.50,
                "high_match": 0.30
            }
        }
        result = classify_to_3quadrant(movie, 0.55, config=custom_config)
        assert result == "q1_perfect_match"


class TestCalculate3QuadrantScore:
    """測試 calculate_3quadrant_score 函數"""
    
    @pytest.mark.unit
    def test_sr015_q1_score_calculation(self):
        """SR-015: Q1 分數計算 (Embedding 50%, Match 20%)"""
        movie = {"match_ratio": 0.80}
        score = calculate_3quadrant_score(
            movie=movie,
            embedding_score=0.60,
            quadrant="q1_perfect_match"
        )
        # 0.60 * 100 * 0.50 + 0.80 * 100 * 0.20 = 30 + 16 = 46
        assert abs(score - 46.0) < 0.01
    
    @pytest.mark.unit
    def test_sr016_q2_score_calculation(self):
        """SR-016: Q2 分數計算 (Embedding 70%, Match 20%)"""
        movie = {"match_ratio": 0.40}
        score = calculate_3quadrant_score(
            movie=movie,
            embedding_score=0.70,
            quadrant="q2_semantic_discovery"
        )
        # 0.70 * 100 * 0.70 + 0.40 * 100 * 0.20 = 49 + 8 = 57
        assert abs(score - 57.0) < 0.01
    
    @pytest.mark.unit
    def test_sr017_q4_score_calculation(self):
        """SR-017: Q4 分數計算 (Embedding 30%, Match 30%)"""
        movie = {"match_ratio": 0.60}
        score = calculate_3quadrant_score(
            movie=movie,
            embedding_score=0.50,
            quadrant="q4_fallback"
        )
        # 0.50 * 100 * 0.30 + 0.60 * 100 * 0.30 = 15 + 18 = 33
        assert abs(score - 33.0) < 0.01
    
    @pytest.mark.unit
    def test_sr018_custom_weights(self):
        """SR-018: 自定義權重"""
        movie = {"match_ratio": 0.50}
        custom_config = {
            "quadrant_weights": {
                "q1_perfect_match": {
                    "embedding": 0.80,
                    "match_ratio": 0.20
                }
            }
        }
        score = calculate_3quadrant_score(
            movie=movie,
            embedding_score=0.60,
            quadrant="q1_perfect_match",
            config=custom_config
        )
        # 0.60 * 100 * 0.80 + 0.50 * 100 * 0.20 = 48 + 10 = 58
        assert abs(score - 58.0) < 0.01


class TestSortByQuadrantAndEmbedding:
    """測試 sort_by_quadrant_and_embedding 函數"""
    
    @pytest.mark.unit
    def test_sr019_quadrant_priority_sorting(self):
        """SR-019: 象限優先排序"""
        movies = [
            {"title": "A", "quadrant": "q4_fallback", "final_score": 50},
            {"title": "B", "quadrant": "q1_perfect_match", "final_score": 80},
            {"title": "C", "quadrant": "q2_semantic_discovery", "final_score": 70},
            {"title": "D", "quadrant": "q1_perfect_match", "final_score": 85}
        ]
        
        sorted_movies = sort_by_quadrant_and_embedding(movies)
        titles = [m["title"] for m in sorted_movies]
        
        # Q1(85) > Q1(80) > Q2(70) > Q4(50)
        assert titles == ["D", "B", "C", "A"]
    
    @pytest.mark.unit
    def test_sr020_same_quadrant_score_sorting(self):
        """SR-020: 同象限內按分數排序"""
        movies = [
            {"title": "A", "quadrant": "q1_perfect_match", "final_score": 60},
            {"title": "B", "quadrant": "q1_perfect_match", "final_score": 80},
            {"title": "C", "quadrant": "q1_perfect_match", "final_score": 70}
        ]
        
        sorted_movies = sort_by_quadrant_and_embedding(movies)
        scores = [m["final_score"] for m in sorted_movies]
        
        assert scores == [80, 70, 60]  # 降序
    
    @pytest.mark.unit
    def test_sr021_empty_list(self):
        """SR-021: 空列表處理"""
        result = sort_by_quadrant_and_embedding([])
        assert result == []


class TestTieredFeatureFiltering:
    """測試 tiered_feature_filtering 函數"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sr022_hard_filters_genre(self):
        """SR-022: Hard Filter - 類型過濾"""
        candidates = [
            {"title": "Drama 1", "genres": ["剧情"], "embedding_score": 0.8},
            {"title": "Action 1", "genres": ["动作"], "embedding_score": 0.7},
            {"title": "Drama 2", "genres": ["剧情"], "embedding_score": 0.6}
        ]
        
        result = await tiered_feature_filtering(
            embedding_candidates=candidates,
            keywords=[],
            mood_tags=[],
            genres=["剧情"],  # 使用簡體中文
            target_count=10
        )
        
        # 應該只保留劇情片
        assert len(result) == 2
        assert all("剧情" in m["genres"] for m in result)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sr023_hard_filters_year_range(self):
        """SR-023: Hard Filter - 年份範圍"""
        candidates = [
            {"title": "Old", "release_date": "2000-01-01", "embedding_score": 0.8},
            {"title": "New", "release_date": "2020-01-01", "embedding_score": 0.7},
            {"title": "Recent", "release_date": "2015-06-15", "embedding_score": 0.6}
        ]
        
        result = await tiered_feature_filtering(
            embedding_candidates=candidates,
            keywords=[],
            mood_tags=[],
            genres=[],
            year_range=(2010, 2025),
            target_count=10
        )
        
        # 只保留 2010-2025
        assert len(result) == 2
        titles = [m["title"] for m in result]
        assert "Old" not in titles
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sr024_hard_filters_min_rating(self):
        """SR-024: Hard Filter - 最低評分"""
        candidates = [
            {"title": "Great", "vote_average": 8.5, "embedding_score": 0.8},
            {"title": "Good", "vote_average": 7.0, "embedding_score": 0.7},
            {"title": "Bad", "vote_average": 5.0, "embedding_score": 0.6}
        ]
        
        result = await tiered_feature_filtering(
            embedding_candidates=candidates,
            keywords=[],
            mood_tags=[],
            genres=[],
            min_rating=7.0,
            target_count=10
        )
        
        # 只保留評分 >= 7.0
        assert len(result) == 2
        assert all(m["vote_average"] >= 7.0 for m in result)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sr025_tiered_filtering_logic(self):
        """SR-025: 三層漸進式過濾邏輯"""
        candidates = [
            {
                "title": "Perfect",
                "keywords": ["love", "family"],
                "mood_tags": ["heartwarming"],
                "genres": ["剧情"],
                "embedding_score": 0.9
            },
            {
                "title": "Medium",
                "keywords": ["love"],
                "mood_tags": [],
                "genres": ["剧情"],
                "embedding_score": 0.7
            },
            {
                "title": "Poor",
                "keywords": [],
                "mood_tags": [],
                "genres": ["剧情"],
                "embedding_score": 0.5
            }
        ]
        
        result = await tiered_feature_filtering(
            embedding_candidates=candidates,
            keywords=["love", "family"],
            mood_tags=["heartwarming"],
            genres=["剧情"],  # 使用簡體中文
            target_count=10
        )
        
        # 應該計算 match_ratio 並排序
        assert len(result) > 0
        assert all("match_ratio" in m for m in result)
        assert result[0]["title"] == "Perfect"  # 最高匹配


class TestRecommendMoviesEmbeddingFirst:
    """測試 recommend_movies_embedding_first 主函數"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sr026_basic_recommendation_flow(self, mock_openai_client):
        """SR-026: 基本推薦流程"""
        # Mock embedding_similarity_search
        mock_candidates = [
            {
                "id": 1,
                "tmdb_id": "550",
                "title": "Fight Club",
                "overview": "Test overview",
                "poster_path": "/test.jpg",
                "vote_average": 8.5,
                "release_date": "1999-10-15",
                "genres": ["剧情"],
                "keywords": ["philosophy"],
                "mood_tags": ["thought-provoking"],
                "embedding_score": 0.75
            }
        ]
        
        with patch('app.services.embedding_query_generator.generate_embedding_query') as mock_query:
            with patch('app.services.embedding_service.embedding_similarity_search', new_callable=AsyncMock) as mock_search:
                mock_query.return_value = {
                    "query": "philosophical movies",
                    "scenario": "nl_only",
                    "conflict": False
                }
                mock_search.return_value = mock_candidates
                
                result = await recommend_movies_embedding_first(
                    natural_query="thought-provoking movies",
                    db_session=Mock(),
                    count=10,
                    config={"debug": {}}  # 傳入最小配置
                )
                
                assert len(result) > 0
                assert result[0]["title"] == "Fight Club"
                assert "embedding_score" in result[0]
                assert "match_ratio" in result[0]
                assert "quadrant" in result[0]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sr027_empty_candidates(self):
        """SR-027: 空候選列表處理"""
        with patch('app.services.embedding_query_generator.generate_embedding_query') as mock_query:
            with patch('app.services.embedding_service.embedding_similarity_search', new_callable=AsyncMock) as mock_search:
                mock_query.return_value = {"query": "test", "scenario": "nl_only"}
                mock_search.return_value = []
                
                result = await recommend_movies_embedding_first(
                    natural_query="test",
                    db_session=Mock(),
                    count=10
                )
                
                assert result == []
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sr028_smart_selection_top3_guaranteed(self, mock_openai_client):
        """SR-028: Smart Selection - Top 3 保證返回"""
        mock_candidates = []
        for i in range(30):
            mock_candidates.append({
                "id": i,
                "tmdb_id": str(i),
                "title": f"Movie {i}",
                "overview": "Test",
                "poster_path": "/test.jpg",
                "vote_average": 7.0,
                "release_date": "2020-01-01",
                "genres": ["剧情"],
                "keywords": [],
                "mood_tags": [],
                "embedding_score": 0.9 - (i * 0.01)  # 遞減
            })
        
        with patch('app.services.embedding_query_generator.generate_embedding_query') as mock_query:
            with patch('app.services.embedding_service.embedding_similarity_search', new_callable=AsyncMock) as mock_search:
                mock_query.return_value = {"query": "test", "scenario": "nl_only"}
                mock_search.return_value = mock_candidates
                
                result = await recommend_movies_embedding_first(
                    natural_query="test",
                    db_session=Mock(),
                    count=10,
                    config={"debug": {}}  # 傳入最小配置
                )
                
                # Top 3 應該是分數最高的
                assert len(result) == 10
                assert result[0]["title"] == "Movie 0"
                assert result[1]["title"] == "Movie 1"
                assert result[2]["title"] == "Movie 2"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sr029_formatted_output_structure(self, mock_openai_client):
        """SR-029: 輸出格式完整性"""
        mock_candidates = [{
            "id": 550,
            "tmdb_id": "550",
            "title": "Fight Club",
            "overview": "A test overview",
            "poster_path": "/test.jpg",
            "vote_average": 8.5,
            "release_date": date(1999, 10, 15),
            "genres": ["剧情"],
            "keywords": ["test"],
            "mood_tags": ["dark"],
            "runtime": 139,
            "actors": ["Brad Pitt"],
            "embedding_score": 0.75
        }]
        
        with patch('app.services.embedding_query_generator.generate_embedding_query') as mock_query:
            with patch('app.services.embedding_service.embedding_similarity_search', new_callable=AsyncMock) as mock_search:
                mock_query.return_value = {"query": "test", "scenario": "nl_only"}
                mock_search.return_value = mock_candidates
                
                result = await recommend_movies_embedding_first(
                    natural_query="test",
                    db_session=Mock(),
                    count=10,
                    config={"debug": {}}  # 傳入最小配置
                )
                
                movie = result[0]
                # 檢查所有必要欄位
                assert "id" in movie
                assert "title" in movie
                assert "overview" in movie
                assert "poster_url" in movie
                assert "vote_average" in movie
                assert "release_year" in movie
                assert "embedding_score" in movie
                assert "match_ratio" in movie
                assert "final_score" in movie
                assert "quadrant" in movie
                assert "genres" in movie
                
                # 檢查格式化正確
                assert movie["release_year"] == 1999
                assert "https://image.tmdb.org/t/p/w500" in movie["poster_url"]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sr030_cache_integration(self, mock_openai_client):
        """SR-030: 快取整合測試"""
        mock_cached_result = [{"title": "Cached Movie"}]
        
        with patch('app.services.recommendation_cache.get_cached_recommendation', return_value=mock_cached_result):
            result = await recommend_movies_embedding_first(
                natural_query="test",
                db_session=Mock(),
                count=10,
                use_cache=True
            )
            
            # 應該直接返回快取結果
            assert result == mock_cached_result
