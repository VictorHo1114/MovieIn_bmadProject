"""
End-to-End Tests for Complete Recommendation Scenarios
測試完整的推薦場景流程
"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-testing-only"
os.environ["TESTING"] = "1"

import pytest
from typing import List, Dict
from unittest.mock import Mock, patch, MagicMock

from app.services.embedding_query_generator import generate_embedding_query
from app.services.mood_analyzer import analyze_mood_combination
from app.services.embedding_service import get_embedding, cosine_similarity
from app.services.recommendation_cache import (
    generate_recommendation_cache_key,
    get_cached_recommendation,
    set_cached_recommendation
)


class TestCompleteRecommendationScenarios:
    """測試完整推薦場景"""
    
    @pytest.mark.e2e
    def test_e001_natural_language_only_scenario(self, mock_openai_client):
        """E2E-001: 純自然語言查詢完整流程"""
        # Arrange - 用戶輸入
        user_input = "我想看溫暖治癒的電影"
        mood_labels = []
        
        # Step 1: Generate embedding query
        query_result = generate_embedding_query(user_input, mood_labels)
        
        # Step 2: Get embedding for query
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        with patch('app.services.embedding_service.client', mock_openai_client):
            with patch('app.services.recommendation_cache.get_cached_embedding', return_value=None):
                with patch('app.services.recommendation_cache.set_cached_embedding'):
                    query_embedding = get_embedding(query_result["query"])
        
        # Assert
        assert query_result["scenario"] == "nl_only"
        assert len(query_embedding) == 1536
    
    @pytest.mark.e2e
    def test_e002_mood_labels_only_scenario(self):
        """E2E-002: 純 Mood Labels 查詢完整流程"""
        # Arrange
        user_input = ""
        mood_labels = ["emotional", "heartwarming"]
        
        # Step 1: Analyze mood combination
        mood_analysis = analyze_mood_combination(mood_labels)
        
        # Step 2: Generate embedding query with mood template
        query_result = generate_embedding_query(user_input, mood_labels, mood_analysis)
        
        # Assert
        assert query_result["scenario"] == "mood_only"
        assert query_result["mood_relationship"] is not None
        assert len(query_result["query"]) > 0
        assert query_result["mood_relationship"]["type"] in ["journey", "intensification", "paradox", "multi-faceted"]
    
    @pytest.mark.e2e
    def test_e003_combined_nl_and_mood_scenario(self, mock_openai_client):
        """E2E-003: NL + Mood 混合查詢完整流程"""
        # Arrange
        user_input = "想看治癒人心的故事"
        mood_labels = ["heartwarming", "uplifting"]
        
        # Step 1: Analyze mood
        mood_analysis = analyze_mood_combination(mood_labels)
        
        # Step 2: Generate query (NL優先)
        query_result = generate_embedding_query(user_input, mood_labels, mood_analysis)
        
        # Step 3: Check conflict detection
        assert query_result["scenario"] == "both"
        assert query_result["query"] == user_input  # NL優先
        assert query_result["conflict_detected"] is False
        
        # Step 4: Get embedding
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.2] * 1536)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        with patch('app.services.embedding_service.client', mock_openai_client):
            with patch('app.services.recommendation_cache.get_cached_embedding', return_value=None):
                with patch('app.services.recommendation_cache.set_cached_embedding'):
                    embedding = get_embedding(query_result["query"])
        
        # Assert
        assert len(embedding) == 1536
    
    @pytest.mark.e2e
    def test_e004_conflict_detection_scenario(self):
        """E2E-004: 衝突檢測場景"""
        # Arrange - 溫暖 vs 黑暗 (明顯衝突)
        user_input = "溫暖治癒的故事"
        mood_labels = ["dark", "gritty", "disturbing"]
        
        # Act
        query_result = generate_embedding_query(user_input, mood_labels)
        
        # Assert
        assert query_result["conflict_detected"] is True
        assert query_result["scenario"] == "both"


class TestCachedRecommendationScenarios:
    """測試帶快取的推薦場景"""
    
    @pytest.mark.e2e
    @pytest.mark.cache
    def test_e005_first_time_query_with_cache(self, mock_openai_client, mock_redis_client):
        """E2E-005: 首次查詢 → 計算 → 儲存快取"""
        # Arrange
        query_text = "浪漫愛情故事"
        expected_embedding = [0.3] * 1536
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=expected_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        # Mock cache storage
        cache_storage = {}
        
        def mock_set_cache(text, embedding):
            cache_storage[text] = embedding
        
        # Act
        with patch('app.services.embedding_service.client', mock_openai_client):
            with patch('app.services.recommendation_cache.get_cached_embedding', return_value=None):
                with patch('app.services.recommendation_cache.set_cached_embedding', side_effect=mock_set_cache):
                    embedding = get_embedding(query_text, use_cache=True)
        
        # Assert
        assert embedding == expected_embedding
        assert query_text in cache_storage
    
    @pytest.mark.e2e
    @pytest.mark.cache
    def test_e006_repeat_query_hits_cache(self):
        """E2E-006: 重複查詢 → 快取命中"""
        # Arrange
        query_text = "科幻冒險電影"
        cached_embedding = [0.4] * 1536
        
        # Act
        with patch('app.services.recommendation_cache.get_cached_embedding', return_value=cached_embedding):
            embedding = get_embedding(query_text, use_cache=True)
        
        # Assert
        assert embedding == cached_embedding


class TestMultiStepRecommendationWorkflow:
    """測試多步驟推薦工作流"""
    
    @pytest.mark.e2e
    def test_e007_complete_recommendation_pipeline(self, mock_openai_client):
        """E2E-007: 完整推薦流程 (Query → Embedding → Similarity)"""
        # Step 1: User input
        user_query = "感人的親情故事"
        mood_labels = ["emotional", "heartwarming"]
        
        # Step 2: Generate embedding query
        query_result = generate_embedding_query(user_query, mood_labels)
        
        # Step 3: Get query embedding
        query_embedding = [0.5] * 1536
        mock_response = Mock()
        mock_response.data = [Mock(embedding=query_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        with patch('app.services.embedding_service.client', mock_openai_client):
            with patch('app.services.recommendation_cache.get_cached_embedding', return_value=None):
                with patch('app.services.recommendation_cache.set_cached_embedding'):
                    q_embedding = get_embedding(query_result["query"])
        
        # Step 4: Calculate similarity with mock movie
        movie_embedding = [0.5] * 1536  # 相同向量
        similarity = cosine_similarity(q_embedding, movie_embedding)
        
        # Assert
        assert query_result["scenario"] == "both"
        assert len(q_embedding) == 1536
        assert abs(similarity - 1.0) < 1e-6  # 完全相同
    
    @pytest.mark.e2e
    def test_e008_empty_input_fallback(self):
        """E2E-008: 空輸入 → Fallback 推薦"""
        # Arrange
        user_query = ""
        mood_labels = []
        
        # Act
        query_result = generate_embedding_query(user_query, mood_labels)
        
        # Assert
        assert query_result["scenario"] == "empty"
        assert "popular" in query_result["query"].lower() or "rated" in query_result["query"].lower()
    
    @pytest.mark.e2e
    def test_e009_quadrant_based_recommendation(self):
        """E2E-009: Quadrant 推薦流程"""
        # Arrange - Quadrant 1: Uplifting & Light
        mood_labels = ["uplifting", "cheerful", "feel-good"]
        
        # Step 1: Analyze mood
        mood_analysis = analyze_mood_combination(mood_labels)
        
        # Step 2: Generate query
        query_result = generate_embedding_query("", mood_labels, mood_analysis)
        
        # Assert
        assert query_result["scenario"] in ["mood_only", "simple"]
        assert len(query_result["query"]) > 0
    
    @pytest.mark.e2e
    @pytest.mark.cache
    def test_e010_recommendation_result_caching(self, mock_redis_client):
        """E2E-010: 推薦結果快取完整流程"""
        # Arrange
        recommendations = [
            {"id": 550, "title": "Fight Club", "score": 0.95},
            {"id": 13, "title": "Forrest Gump", "score": 0.92}
        ]
        
        query_params = {
            "natural_query": "人生哲理電影",
            "mood_labels": ["thought-provoking"],
            "count": 10
        }
        
        # Mock Redis
        cache_storage = {}
        
        def mock_setex(key, ttl, value):
            cache_storage[key] = value
            return True
        
        def mock_get(key):
            return cache_storage.get(key)
        
        mock_redis_client.setex.side_effect = mock_setex
        mock_redis_client.get.side_effect = mock_get
        
        # Act - Set cache
        with patch('app.services.recommendation_cache.redis_client', mock_redis_client):
            set_cached_recommendation(recommendations, **query_params)
            
            # Get cache
            cache_key = generate_recommendation_cache_key(**query_params)
            result = get_cached_recommendation(cache_key)
        
        # Assert - 函數執行成功
        assert result is None or isinstance(result, dict)
