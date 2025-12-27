"""
Integration Tests for Database Operations
測試資料庫操作整合
"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-testing-only"
os.environ["TESTING"] = "1"

import pytest
from typing import List, Dict
from unittest.mock import Mock, patch

from app.services.embedding_service import (
    store_movie_embedding,
    get_stored_embeddings
)


class TestDatabaseEmbeddingOperations:
    """測試資料庫 Embedding 操作"""
    
    @pytest.mark.integration
    @pytest.mark.db
    def test_i013_store_and_retrieve_embedding(self, mock_openai_client):
        """I-013: 儲存並檢索 Embedding"""
        # Arrange
        tmdb_id = 12345
        overview = "A great adventure movie"
        expected_embedding = [0.2] * 1536
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=expected_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        # Create mock DB session
        mock_db_session = Mock()
        
        # Act - Store
        with patch('app.services.embedding_service.client', mock_openai_client):
            with patch('app.services.recommendation_cache.get_cached_embedding', return_value=None):
                with patch('app.services.recommendation_cache.set_cached_embedding'):
                    store_movie_embedding(mock_db_session, tmdb_id, overview)
        
        # Assert
        assert mock_db_session.execute.called
        assert mock_db_session.commit.called
    
    @pytest.mark.integration
    @pytest.mark.db
    async def test_i014_batch_retrieve_embeddings(self):
        """I-014: 批次檢索多部電影的 Embeddings"""
        # Arrange
        tmdb_ids = [123, 456, 789]
        
        # Mock DB session with embeddings
        mock_db_session = Mock()
        mock_rows = [
            (123, [0.1] * 100),
            (456, [0.2] * 100),
            (789, [0.3] * 100)
        ]
        mock_db_session.execute.return_value = mock_rows
        
        # Act
        result = await get_stored_embeddings(mock_db_session, tmdb_ids)
        
        # Assert
        assert len(result) == 3
        assert 123 in result
        assert 456 in result
        assert 789 in result
