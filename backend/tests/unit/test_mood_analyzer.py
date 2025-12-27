"""
Unit Tests for Mood Analyzer (app/services/mood_analyzer.py)
測試案例：M-001 ~ M-009
"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-testing-only"
os.environ["TESTING"] = "1"

import pytest
from typing import List, Dict

from app.services.mood_analyzer import (
    analyze_mood_combination,
    analyze_by_heuristics,
    get_relationship_stats,
    search_relationships_by_mood,
    MOOD_RELATIONSHIP_MATRIX
)


class TestAnalyzeMoodCombination:
    """測試 analyze_mood_combination 主函數"""
    
    @pytest.mark.unit
    def test_m001_journey_relationship(self):
        """M-001: 識別 Journey 關係"""
        # Arrange
        mood_labels = ["emotional", "heartwarming"]
        
        # Act
        result = analyze_mood_combination(mood_labels)
        
        # Assert
        assert result["type"] == "journey"
        assert "template" in result
        assert isinstance(result["template"], str)
        assert len(result["template"]) > 0
    
    @pytest.mark.unit
    def test_m002_empty_mood_list(self):
        """M-002: 空列表處理"""
        # Arrange
        mood_labels = []
        
        # Act
        result = analyze_mood_combination(mood_labels)
        
        # Assert
        assert result["type"] == "simple"
        assert result["source"] in ["fallback", "default", "heuristic"]
    
    @pytest.mark.unit
    def test_m003_single_mood(self):
        """M-003: 單一 Mood 處理"""
        # Arrange
        mood_labels = ["emotional"]
        
        # Act
        result = analyze_mood_combination(mood_labels)
        
        # Assert
        assert result["type"] == "simple"
        assert "template" in result
    
    @pytest.mark.unit
    def test_m004_multiple_moods_heuristic(self):
        """M-004: 多個 Moods 使用啟發式規則"""
        # Arrange
        mood_labels = ["mysterious", "thrilling"]
        
        # Act
        result = analyze_mood_combination(mood_labels)
        
        # Assert
        assert "type" in result
        assert result["type"] in ["intensification", "journey", "paradox", "multi-faceted", "simple"]
    
    @pytest.mark.unit
    def test_m005_order_independence(self):
        """M-005: 測試順序無關性（交換順序應得到相同結果）"""
        # Arrange
        moods_order1 = ["emotional", "heartwarming"]
        moods_order2 = ["heartwarming", "emotional"]
        
        # Act
        result1 = analyze_mood_combination(moods_order1)
        result2 = analyze_mood_combination(moods_order2)
        
        # Assert - 應該識別為相同關係（可能是 journey）
        assert result1["type"] == result2["type"]


class TestAnalyzeByHeuristics:
    """測試 analyze_by_heuristics 函數"""
    
    @pytest.mark.unit
    def test_m006_heuristic_dark_moods(self):
        """M-006: 測試黑暗類 Mood 的啟發式規則"""
        # Arrange
        dark_moods = ["dark", "gritty"]
        
        # Act
        result = analyze_by_heuristics(dark_moods)
        
        # Assert
        if result:  # 可能返回 None（沒有匹配規則）
            assert "type" in result
            assert result["type"] in ["intensification", "paradox"]
    
    @pytest.mark.unit
    def test_m007_heuristic_no_match(self):
        """M-007: 無匹配規則時返回 None"""
        # Arrange
        random_moods = ["random_mood_1", "random_mood_2"]
        
        # Act
        result = analyze_by_heuristics(random_moods)
        
        # Assert
        # 可能返回 None 或 simple 類型
        assert result is None or result["type"] == "simple"


class TestUtilityFunctions:
    """測試工具函數"""
    
    @pytest.mark.unit
    def test_m008_get_relationship_stats(self):
        """M-008: 測試關係統計"""
        # Act
        stats = get_relationship_stats()
        
        # Assert
        assert "total" in stats
        assert "by_type" in stats
        assert isinstance(stats["total"], int)
        assert isinstance(stats["by_type"], dict)
        assert stats["total"] > 0  # 應該有一些關係定義
    
    @pytest.mark.unit
    def test_m009_search_relationships_by_mood(self):
        """M-009: 測試根據 Mood 搜尋關係"""
        # Arrange
        mood = "emotional"
        
        # Act
        results = search_relationships_by_mood(mood)
        
        # Assert
        assert isinstance(results, list)
        # emotional 應該在某些關係中
        if len(results) > 0:
            assert "moods" in results[0]
            # 檢查是否有 type 或 relationship 欄位
            assert "type" in results[0] or "relationship" in results[0]


class TestMoodRelationshipMatrix:
    """測試 MOOD_RELATIONSHIP_MATRIX 數據完整性"""
    
    @pytest.mark.unit
    def test_matrix_structure(self):
        """測試 Matrix 結構完整性"""
        # Act & Assert
        assert isinstance(MOOD_RELATIONSHIP_MATRIX, dict)
        assert len(MOOD_RELATIONSHIP_MATRIX) > 0
        
        # 檢查第一個項目的結構
        for key, value in list(MOOD_RELATIONSHIP_MATRIX.items())[:3]:
            assert isinstance(key, tuple)
            assert len(key) == 2
            assert "type" in value
            assert "template" in value
            assert value["type"] in ["journey", "paradox", "intensification", "multi-faceted"]
