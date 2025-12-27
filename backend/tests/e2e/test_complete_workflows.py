"""
End-to-End Tests for Complete Recommendation Workflows
測試完整的推薦工作流程（從用戶輸入到結果返回）
"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-testing-only"
os.environ["TESTING"] = "1"

import pytest
from typing import List, Dict
from unittest.mock import Mock, patch

from app.services.embedding_query_generator import generate_embedding_query
from app.services.mood_analyzer import analyze_mood_combination
from app.services.embedding_service import get_embedding, cosine_similarity


class TestUserJourneyWorkflows:
    """測試用戶旅程工作流"""
    
    @pytest.mark.e2e
    def test_e011_new_user_first_recommendation(self, mock_openai_client):
        """E2E-011: 新用戶首次推薦流程"""
        # Arrange - 新用戶輸入
        user_input = "想看讓人開心的電影"
        
        # Step 1: Generate query
        query_result = generate_embedding_query(user_input, [])
        
        # Step 2: Get embedding
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.6] * 1536)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        with patch('app.services.embedding_service.client', mock_openai_client):
            with patch('app.services.recommendation_cache.get_cached_embedding', return_value=None):
                with patch('app.services.recommendation_cache.set_cached_embedding'):
                    embedding = get_embedding(query_result["query"])
        
        # Assert
        assert query_result["scenario"] == "nl_only"
        assert len(embedding) == 1536
    
    @pytest.mark.e2e
    def test_e012_mood_quadrant_selection_workflow(self):
        """E2E-012: Mood Quadrant 選擇工作流"""
        # Arrange - 用戶選擇 Quadrant 2: Deep & Thoughtful
        selected_moods = ["thought-provoking", "philosophical", "contemplative"]
        
        # Step 1: Analyze mood combination
        mood_analysis = analyze_mood_combination(selected_moods)
        
        # Step 2: Generate template query
        query_result = generate_embedding_query("", selected_moods, mood_analysis)
        
        # Assert
        assert query_result["scenario"] in ["mood_only", "simple"]
        assert query_result["mood_relationship"] is not None
        assert "thought" in query_result["query"].lower() or "philosophical" in query_result["query"].lower()
    
    @pytest.mark.e2e
    def test_e013_refined_search_workflow(self):
        """E2E-013: 精煉搜尋工作流（NL + Mood）"""
        # Arrange - 用戶輸入 + 選擇 Mood
        user_input = "關於家庭的故事"
        selected_moods = ["heartwarming", "emotional"]
        
        # Step 1: Analyze mood
        mood_analysis = analyze_mood_combination(selected_moods)
        
        # Step 2: Generate query (NL優先，Mood用於過濾)
        query_result = generate_embedding_query(user_input, selected_moods, mood_analysis)
        
        # Assert
        assert query_result["scenario"] == "both"
        assert query_result["query"] == user_input
        assert query_result["mood_relationship"]["type"] in ["journey", "intensification"]
    
    @pytest.mark.e2e
    def test_e014_multi_round_refinement_workflow(self, mock_openai_client):
        """E2E-014: 多輪精煉工作流"""
        # Round 1: Initial broad query
        query1 = "科幻電影"
        result1 = generate_embedding_query(query1, [])
        
        # Round 2: Add mood refinement
        query2 = query1
        moods2 = ["thrilling", "suspenseful"]
        result2 = generate_embedding_query(query2, moods2)
        
        # Round 3: More specific query
        query3 = "時間旅行的科幻電影"
        moods3 = moods2
        result3 = generate_embedding_query(query3, moods3)
        
        # Assert - 每輪查詢都應該正常處理
        assert result1["scenario"] == "nl_only"
        assert result2["scenario"] == "both"
        assert result3["scenario"] == "both"
        assert result3["query"] == query3


class TestEdgeCaseWorkflows:
    """測試邊界情況工作流"""
    
    @pytest.mark.e2e
    def test_e015_very_long_query_workflow(self, mock_openai_client):
        """E2E-015: 超長查詢處理"""
        # Arrange
        long_query = "我想看一部關於" + "非常感人" * 50 + "的電影"
        
        # Act
        query_result = generate_embedding_query(long_query, [])
        
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.7] * 1536)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        with patch('app.services.embedding_service.client', mock_openai_client):
            with patch('app.services.recommendation_cache.get_cached_embedding', return_value=None):
                with patch('app.services.recommendation_cache.set_cached_embedding'):
                    embedding = get_embedding(query_result["query"])
        
        # Assert
        assert len(embedding) == 1536
    
    @pytest.mark.e2e
    def test_e016_special_characters_query_workflow(self):
        """E2E-016: 特殊字符查詢處理"""
        # Arrange
        special_query = "電影🎬🎥❤️✨"
        
        # Act
        query_result = generate_embedding_query(special_query, [])
        
        # Assert
        assert query_result["scenario"] == "nl_only"
        assert len(query_result["query"]) > 0
    
    @pytest.mark.e2e
    def test_e017_many_moods_workflow(self):
        """E2E-017: 多個 Mood Labels 處理"""
        # Arrange - 用戶選擇很多 moods
        many_moods = ["emotional", "heartwarming", "uplifting", "inspiring", "feel-good", "cheerful"]
        
        # Act
        mood_analysis = analyze_mood_combination(many_moods)
        query_result = generate_embedding_query("", many_moods, mood_analysis)
        
        # Assert
        assert query_result["scenario"] in ["mood_only", "simple"]
        assert query_result["mood_relationship"] is not None
    
    @pytest.mark.e2e
    def test_e018_contradictory_moods_workflow(self):
        """E2E-018: 矛盾 Mood Labels 處理"""
        # Arrange - 矛盾的 moods
        contradictory_moods = ["cheerful", "dark", "uplifting", "disturbing"]
        
        # Act
        mood_analysis = analyze_mood_combination(contradictory_moods)
        query_result = generate_embedding_query("", contradictory_moods, mood_analysis)
        
        # Assert
        assert query_result["scenario"] in ["mood_only", "simple"]
        # 應該能處理，即使矛盾


class TestPerformanceWorkflows:
    """測試性能相關工作流"""
    
    @pytest.mark.e2e
    def test_e019_similarity_calculation_batch(self):
        """E2E-019: 批次相似度計算"""
        # Arrange
        query_embedding = [0.5] * 1536
        movie_embeddings = [
            [0.5] * 1536,  # 完全相同
            [0.4] * 1536,  # 相似
            [-0.5] * 1536, # 相反
            [0.0] * 1536,  # 零向量
        ]
        
        # Act
        similarities = [
            cosine_similarity(query_embedding, movie_emb)
            for movie_emb in movie_embeddings
        ]
        
        # Assert
        assert len(similarities) == 4
        assert abs(similarities[0] - 1.0) < 1e-6  # 相同向量
        assert 0.0 < similarities[1] < 1.0  # 相似向量
        assert similarities[2] < 0.0  # 相反向量
        assert similarities[3] == 0.0  # 零向量
    
    @pytest.mark.e2e
    def test_e020_cache_performance_simulation(self, mock_openai_client):
        """E2E-020: 快取性能模擬"""
        # Simulate: 1st query - miss, 2nd query - hit
        query_text = "快取測試查詢"
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.7] * 1536)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        # First call - cache miss
        with patch('app.services.embedding_service.client', mock_openai_client):
            with patch('app.services.recommendation_cache.get_cached_embedding', return_value=None):
                with patch('app.services.recommendation_cache.set_cached_embedding'):
                    result1 = get_embedding(query_text, use_cache=True)
        
        # Second call - cache hit
        cached_embedding = [0.8] * 1536
        with patch('app.services.recommendation_cache.get_cached_embedding', return_value=cached_embedding):
            result2 = get_embedding(query_text, use_cache=True)
        
        # Assert
        assert len(result1) == 1536
        assert result2 == cached_embedding
