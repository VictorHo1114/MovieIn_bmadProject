"""
Unit Tests for Embedding Service - Database Operations
Tests: E-011 to E-020 (Database and batch operations)
"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-testing-only"
os.environ["TESTING"] = "1"

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock

from app.services.embedding_service import (
    store_movie_embedding,
    get_stored_embeddings,
    rerank_by_semantic_similarity,
    embedding_similarity_search,
    EMBEDDING_DIM
)


class TestStoreMovieEmbeddingDB:
    """Test store_movie_embedding database operations"""
    
    @pytest.mark.unit
    def test_e011_store_new_embedding(self, mock_openai_client):
        """E-011: Store new movie embedding"""
        mock_db = Mock()
        tmdb_id = 12345
        overview = "A great adventure movie"
        expected_embedding = [0.5] * EMBEDDING_DIM
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=expected_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        with patch("app.services.embedding_service.client", mock_openai_client):
            with patch("app.services.recommendation_cache.get_cached_embedding", return_value=None):
                with patch("app.services.recommendation_cache.set_cached_embedding"):
                    store_movie_embedding(mock_db, tmdb_id, overview)
        
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()


class TestGetStoredEmbeddingsDB:
    """Test get_stored_embeddings batch operations"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_e015_get_embeddings_basic(self):
        """E-015: Basic batch retrieval"""
        mock_db = Mock()
        tmdb_ids = [1, 2, 3]
        
        # Mock the iterator behavior
        mock_result = [
            (1, json.dumps([0.1] * EMBEDDING_DIM)),
            (2, json.dumps([0.2] * EMBEDDING_DIM)),
            (3, json.dumps([0.3] * EMBEDDING_DIM))
        ]
        mock_db.execute.return_value = mock_result
        
        result = await get_stored_embeddings(mock_db, tmdb_ids)
        
        assert len(result) == 3
        assert 1 in result
        assert 2 in result
        assert 3 in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_e017_get_embeddings_empty_list(self):
        """E-017: Empty tmdb_ids list"""
        mock_db = Mock()
        result = await get_stored_embeddings(mock_db, [])
        
        assert result == {}
        mock_db.execute.assert_not_called()


class TestRerankBySemantic:
    """Test rerank_by_semantic_similarity"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("app.services.embedding_service.get_stored_embeddings")
    @patch("app.services.embedding_service.get_embedding")
    async def test_e019_rerank_all_cached(self, mock_get_emb, mock_get_stored):
        """E-019: All movies have cached embeddings"""
        mock_db = Mock()
        query_text = "action movie"
        candidate_movies = [
            {"id": 1, "title": "Movie 1", "overview": "Action"},
            {"id": 2, "title": "Movie 2", "overview": "Drama"}
        ]
        
        query_embedding = [0.5] * EMBEDDING_DIM
        mock_get_emb.return_value = query_embedding
        
        stored_embeddings = {
            1: [0.6] * EMBEDDING_DIM,
            2: [0.4] * EMBEDDING_DIM
        }
        mock_get_stored.return_value = stored_embeddings
        
        result = await rerank_by_semantic_similarity(query_text, candidate_movies, mock_db)
        
        assert len(result) == 2
        assert all("similarity_score" in m for m in result)


class TestEmbeddingSimilaritySearch:
    """Test embedding_similarity_search pgvector operations"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("app.services.embedding_service.get_embedding")
    async def test_e026_search_basic(self, mock_get_emb):
        """E-026: Basic pgvector search"""
        from unittest.mock import MagicMock
        
        # Use MagicMock to support iteration and other operations
        mock_db = MagicMock()
        query_text = "space adventure"  # Real string, not Mock
        
        query_embedding = [0.5] * EMBEDDING_DIM
        mock_get_emb.return_value = query_embedding
        
        # Mock execute to return fetchall()-like behavior
        mock_rows = [
            (1, "space epic", "Star Wars", "Star Wars", "In space", "1977-05-25",
             100.0, 8.5, 5000, ["Action"], ["space"], ["epic"], "/poster.jpg", 0.95)
        ]
        mock_db.execute.return_value.fetchall.return_value = mock_rows
        
        # Correct parameter order: query_text, db_session
        result = await embedding_similarity_search(query_text, mock_db, top_k=10)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["embedding_score"] == 0.95
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("app.services.embedding_service.get_embedding")
    async def test_e027_search_no_results(self, mock_get_emb):
        """E-027: No results from pgvector"""
        from unittest.mock import MagicMock
        
        mock_db = MagicMock()
        query_text = "nonexistent query"  # Real string
        
        mock_get_emb.return_value = [0.5] * EMBEDDING_DIM
        
        # Empty result
        mock_db.execute.return_value.fetchall.return_value = []
        
        # Correct parameter order: query_text, db_session
        result = await embedding_similarity_search(query_text, mock_db)
        
        assert result == []
