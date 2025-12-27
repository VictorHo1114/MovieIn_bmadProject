"""
Integration Tests for Recommendation Pipeline
測試完整推薦流程的整合
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


class TestEmbeddingQueryPipeline:
    """測試 Embedding Query 生成流程"""
    
    @pytest.mark.integration
    def test_i001_nl_to_embedding_query(self):
        """I-001: 自然語言 → Embedding Query 完整流程"""
        # Arrange
        natural_query = "我想看溫暖治癒的電影"
        mood_labels = []
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["scenario"] == "nl_only"
        assert result["query"] == natural_query
        assert result["conflict_detected"] is False
    
    @pytest.mark.integration
    def test_i002_mood_to_template_query(self):
        """I-002: Mood Labels → Template → Embedding Query"""
        # Arrange
        mood_labels = ["emotional", "heartwarming"]
        
        # Act - Step 1: Analyze mood combination
        mood_relationship = analyze_mood_combination(mood_labels)
        
        # Act - Step 2: Generate query with mood relationship
        result = generate_embedding_query("", mood_labels, mood_relationship)
        
        # Assert
        assert result["scenario"] == "mood_only"
        assert len(result["query"]) > 0
        assert result["mood_relationship"]["type"] in ["journey", "intensification", "paradox", "multi-faceted"]
    
    @pytest.mark.integration
    def test_i003_combined_input_processing(self):
        """I-003: NL + Mood 混合輸入處理"""
        # Arrange
        natural_query = "溫暖的故事"
        mood_labels = ["heartwarming", "uplifting"]
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["scenario"] == "both"
        assert result["query"] == natural_query  # NL 優先
        assert result["mood_relationship"] is not None


class TestEmbeddingPipeline:
    """測試 Embedding 計算流程"""
    
    @pytest.mark.integration
    def test_i004_query_to_embedding_vector(self, mock_openai_client):
        """I-004: Query Text → Embedding Vector"""
        # Arrange
        query_text = "A heartwarming story about friendship"
        expected_embedding = [0.1] * 1536
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=expected_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        # Act
        with patch('app.services.embedding_service.client', mock_openai_client):
            with patch('app.services.recommendation_cache.get_cached_embedding', return_value=None):
                with patch('app.services.recommendation_cache.set_cached_embedding'):
                    embedding = get_embedding(query_text)
        
        # Assert
        assert len(embedding) == 1536
        assert embedding == expected_embedding
    
    @pytest.mark.integration
    def test_i005_similarity_calculation_pipeline(self, mock_openai_client):
        """I-005: Query Embedding → Movie Embedding → Similarity Score"""
        # Arrange
        query_embedding = [0.5] * 1536
        movie_embedding = [0.5] * 1536
        
        # Act
        similarity = cosine_similarity(query_embedding, movie_embedding)
        
        # Assert
        assert -1.0 <= similarity <= 1.0 + 1e-10  # 允許浮點數誤差
        assert abs(similarity - 1.0) < 1e-6  # 相同向量應該接近 1.0


class TestCacheIntegrationInPipeline:
    """測試快取在推薦流程中的整合"""
    
    @pytest.mark.integration
    @pytest.mark.cache
    def test_i006_embedding_cache_hit_in_pipeline(self):
        """I-006: Embedding 快取命中流程"""
        # Arrange
        query_text = "Cached query"
        cached_embedding = [0.3] * 1536
        
        # Act
        with patch('app.services.recommendation_cache.get_cached_embedding', return_value=cached_embedding):
            embedding = get_embedding(query_text, use_cache=True)
        
        # Assert
        assert embedding == cached_embedding
    
    @pytest.mark.integration
    @pytest.mark.cache
    def test_i007_cache_miss_then_compute(self, mock_openai_client):
        """I-007: 快取未命中 → 計算 → 儲存快取"""
        # Arrange
        query_text = "New query"
        computed_embedding = [0.7] * 1536
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=computed_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        # Mock cache functions
        cache_storage = {}
        
        def mock_get_cache(text):
            return cache_storage.get(text)
        
        def mock_set_cache(text, embedding):
            cache_storage[text] = embedding
        
        # Act
        with patch('app.services.embedding_service.client', mock_openai_client):
            with patch('app.services.recommendation_cache.get_cached_embedding', side_effect=mock_get_cache):
                with patch('app.services.recommendation_cache.set_cached_embedding', side_effect=mock_set_cache):
                    # First call - cache miss
                    embedding1 = get_embedding(query_text)
                    
                    # Second call - cache hit
                    embedding2 = get_embedding(query_text)
        
        # Assert
        assert embedding1 == computed_embedding
        assert embedding2 == computed_embedding
        assert query_text in cache_storage


class TestErrorHandlingInPipeline:
    """測試錯誤處理流程"""
    
    @pytest.mark.integration
    def test_i008_empty_input_handling(self):
        """I-008: 空輸入處理"""
        # Act
        result = generate_embedding_query("", [])
        
        # Assert
        assert result["scenario"] == "empty"
        assert "popular" in result["query"].lower() or "rated" in result["query"].lower()
    
    @pytest.mark.integration
    def test_i009_conflict_detection_pipeline(self):
        """I-009: 衝突檢測完整流程"""
        # Arrange - 溫暖 vs 黑暗 (衝突)
        natural_query = "溫暖治癒的故事"
        mood_labels = ["dark", "gritty"]
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["scenario"] == "both"
        assert result["conflict_detected"] is True
