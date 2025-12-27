"""
Unit Tests for Embedding Query Generator (app/services/embedding_query_generator.py)
測試案例：Q-001 ~ Q-009
"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-testing-only"
os.environ["TESTING"] = "1"

import pytest
from unittest.mock import Mock, patch

from app.services.embedding_query_generator import (
    generate_embedding_query,
    generate_mood_template,
    detect_sentiment_conflict
)


class TestGenerateEmbeddingQuery:
    """測試 generate_embedding_query 函數"""
    
    @pytest.mark.unit
    def test_q001_nl_only_scenario(self):
        """Q-001: 僅自然語言輸入"""
        # Arrange
        natural_query = "難過的時候適合看什麼電影"
        mood_labels = []
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["query"] == natural_query
        assert result["scenario"] == "nl_only"
        assert result["mood_relationship"] is None
        assert result["conflict_detected"] is False
    
    @pytest.mark.unit
    def test_q002_mood_only_scenario(self):
        """Q-002: 僅 Mood Labels 輸入"""
        # Arrange
        natural_query = ""
        mood_labels = ["emotional", "heartwarming"]
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["scenario"] == "mood_only"
        assert isinstance(result["query"], str)
        assert len(result["query"]) > 0
        assert result["mood_relationship"] is not None
        assert result["conflict_detected"] is False
    
    @pytest.mark.unit
    def test_q003_both_scenario_no_conflict(self):
        """Q-003: NL + Mood 無衝突"""
        # Arrange
        natural_query = "溫暖治癒的故事"
        mood_labels = ["heartwarming", "comforting"]
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["scenario"] == "both"
        assert result["query"] == natural_query  # NL 優先
        assert result["mood_relationship"] is not None
        assert result["conflict_detected"] is False
    
    @pytest.mark.unit
    def test_q004_both_scenario_with_conflict(self):
        """Q-004: NL + Mood 有衝突"""
        # Arrange
        natural_query = "溫暖治癒的電影"
        mood_labels = ["dark", "gritty"]
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["scenario"] == "both"
        assert result["query"] == natural_query
        assert result["conflict_detected"] is True
    
    @pytest.mark.unit
    def test_q005_empty_input(self):
        """Q-005: 空輸入處理"""
        # Arrange
        natural_query = ""
        mood_labels = []
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["scenario"] == "empty"
        assert result["query"] == "popular and highly rated movies"
        assert result["mood_relationship"] is None
    
    @pytest.mark.unit
    def test_q006_none_natural_query(self):
        """Q-006: None 輸入處理"""
        # Arrange
        natural_query = None
        mood_labels = ["emotional"]
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["scenario"] == "mood_only"
        assert isinstance(result["query"], str)


class TestGenerateMoodTemplate:
    """測試 generate_mood_template 函數"""
    
    @pytest.mark.unit
    def test_q007_journey_template(self):
        """Q-007: Journey 類型模板生成"""
        # Arrange
        mood_labels = ["sad", "hopeful"]
        relationship = {
            "type": "journey",
            "template": "simple"
        }
        
        # Act
        result = generate_mood_template(mood_labels, relationship)
        
        # Assert
        assert isinstance(result, str)
        assert "transformation" in result.lower() or "journey" in result.lower()
    
    @pytest.mark.unit
    def test_q008_use_matrix_template(self):
        """Q-008: 使用 Matrix 中的模板"""
        # Arrange
        mood_labels = ["emotional", "heartwarming"]
        relationship = {
            "type": "journey",
            "template": "A heartwarming story about emotional healing and personal growth"
        }
        
        # Act
        result = generate_mood_template(mood_labels, relationship)
        
        # Assert
        assert result == relationship["template"]


class TestDetectSentimentConflict:
    """測試 detect_sentiment_conflict 函數"""
    
    @pytest.mark.unit
    def test_q009_conflict_detected(self):
        """Q-009: 衝突檢測（正面 vs 負面）"""
        # Test Case 1: 溫暖 vs 黑暗
        conflict1 = detect_sentiment_conflict(
            "溫暖治癒的故事",
            ["dark", "gritty"]
        )
        assert conflict1 is True
        
        # Test Case 2: 黑暗 vs 溫暖
        conflict2 = detect_sentiment_conflict(
            "dark and gritty thriller",
            ["cheerful", "lighthearted"]
        )
        assert conflict2 is True
        
        # Test Case 3: 無衝突
        no_conflict = detect_sentiment_conflict(
            "溫暖治癒的故事",
            ["heartwarming", "comforting"]
        )
        assert no_conflict is False
        
        # Test Case 4: 無關鍵詞
        neutral = detect_sentiment_conflict(
            "一部電影",
            ["dramatic"]
        )
        assert neutral is False
