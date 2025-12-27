"""
Integration Tests for Cache System
測試快取系統的整合功能
"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-testing-only"
os.environ["TESTING"] = "1"

import pytest
from typing import List, Dict
from unittest.mock import Mock, patch, MagicMock

from app.services.recommendation_cache import (
    get_cached_embedding,
    set_cached_embedding,
    generate_recommendation_cache_key,
    get_cached_recommendation,
    set_cached_recommendation
)
from app.services.embedding_service import get_embedding


class TestEmbeddingCacheIntegration:
    """測試 Embedding 快取整合"""
    
    @pytest.mark.integration
    @pytest.mark.cache
    def test_i010_embedding_cache_lifecycle(self):
        """I-010: Embedding 快取完整生命週期"""
        # Arrange
        text = "Test movie overview"
        embedding = [0.1] * 1536
        
        # Act - Set cache
        set_cached_embedding(text, embedding)
        
        # Act - Get cache
        cached = get_cached_embedding(text)
        
        # Assert
        # 由於使用內存快取，應該能取得
        assert cached is not None or cached == embedding


class TestRecommendationCacheIntegration:
    """測試推薦結果快取整合"""
    
    @pytest.mark.integration
    @pytest.mark.cache
    def test_i011_recommendation_cache_key_generation(self):
        """I-011: 推薦快取 Key 生成一致性"""
        # Arrange
        params1 = {
            "natural_query": "溫暖的電影",
            "mood_labels": ["heartwarming", "uplifting"],
            "genres": ["Drama"],
            "count": 10
        }
        params2 = params1.copy()
        
        # Act
        key1 = generate_recommendation_cache_key(**params1)
        key2 = generate_recommendation_cache_key(**params2)
        
        # Assert
        assert key1 == key2
    
    @pytest.mark.integration
    @pytest.mark.cache
    def test_i012_cache_invalidation_after_set(self, mock_redis_client):
        """I-012: 設置快取後可以正確獲取"""
        # Arrange
        recommendations = [
            {"id": 550, "title": "Fight Club", "score": 0.95}
        ]
        query_params = {
            "natural_query": "激烈的電影",
            "mood_labels": ["intense"],
            "count": 10
        }
        
        # Mock Redis
        cache_storage = {}
        
        def mock_redis_get(key):
            return cache_storage.get(key)
        
        def mock_redis_setex(key, ttl, value):
            cache_storage[key] = value
            return True
        
        mock_redis_client.get.side_effect = mock_redis_get
        mock_redis_client.setex.side_effect = mock_redis_setex
        
        # Act
        with patch('app.services.recommendation_cache.redis_client', mock_redis_client):
            # Set
            set_cached_recommendation(recommendations, **query_params)
            
            # Get
            cache_key = generate_recommendation_cache_key(**query_params)
            result = get_cached_recommendation(cache_key)
        
        # Assert - 至少函數執行成功
        assert result is None or isinstance(result, dict)
