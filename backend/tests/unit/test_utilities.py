"""
Unit Tests for Utility Functions
測試案例：U-001 ~ U-010
測試各種通用輔助函數
"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-testing-only"
os.environ["TESTING"] = "1"

import pytest
import json
import numpy as np
from typing import List, Dict
from datetime import datetime


class TestListManipulation:
    """測試列表操作"""
    
    @pytest.mark.unit
    def test_u001_list_deduplication(self):
        """U-001: 列表去重功能"""
        # 使用字典去重保持順序
        def deduplicate_by_key(items: List[Dict], key: str) -> List[Dict]:
            seen = set()
            result = []
            for item in items:
                if item[key] not in seen:
                    seen.add(item[key])
                    result.append(item)
            return result
        
        # Arrange
        movies = [
            {"id": 1, "title": "Movie A"},
            {"id": 2, "title": "Movie B"},
            {"id": 1, "title": "Movie A"},  # 重複
            {"id": 3, "title": "Movie C"}
        ]
        
        # Act
        result = deduplicate_by_key(movies, "id")
        
        # Assert
        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
        assert result[2]["id"] == 3
    
    @pytest.mark.unit
    def test_u002_list_chunking(self):
        """U-002: 列表分塊處理"""
        def chunk_list(items: List, chunk_size: int) -> List[List]:
            return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        
        # Arrange
        items = list(range(10))
        
        # Act
        chunks = chunk_list(items, 3)
        
        # Assert
        assert len(chunks) == 4  # [0,1,2], [3,4,5], [6,7,8], [9]
        assert chunks[0] == [0, 1, 2]
        assert chunks[3] == [9]


class TestDictManipulation:
    """測試字典操作"""
    
    @pytest.mark.unit
    def test_u003_safe_dict_get(self):
        """U-003: 安全的字典取值"""
        def safe_get(d: Dict, *keys, default=None):
            """支持多層嵌套取值"""
            for key in keys:
                if isinstance(d, dict):
                    d = d.get(key, default)
                else:
                    return default
            return d
        
        # Arrange
        data = {
            "movie": {
                "details": {
                    "title": "Test Movie"
                }
            }
        }
        
        # Act & Assert
        assert safe_get(data, "movie", "details", "title") == "Test Movie"
        assert safe_get(data, "movie", "missing", "title", default="N/A") == "N/A"
        assert safe_get(data, "missing") is None
    
    @pytest.mark.unit
    def test_u004_dict_merge(self):
        """U-004: 字典合並"""
        # Arrange
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        
        # Act
        result = {**dict1, **dict2}
        
        # Assert
        assert result == {"a": 1, "b": 3, "c": 4}
        assert dict2["b"] == 3  # dict2 覆蓋 dict1


class TestStringProcessing:
    """測試字符串處理"""
    
    @pytest.mark.unit
    def test_u005_truncate_string(self):
        """U-005: 字符串截斷"""
        def truncate(text: str, max_length: int, suffix: str = "...") -> str:
            if len(text) <= max_length:
                return text
            return text[:max_length - len(suffix)] + suffix
        
        # Arrange
        long_text = "This is a very long movie overview"
        
        # Act
        result = truncate(long_text, 20)
        
        # Assert
        assert len(result) == 20
        assert result.endswith("...")
        assert result == "This is a very lo..."
    
    @pytest.mark.unit
    def test_u006_normalize_whitespace(self):
        """U-006: 規範化空白字符"""
        def normalize_whitespace(text: str) -> str:
            return " ".join(text.split())
        
        # Arrange
        messy_text = "  Multiple   spaces\n\n  and   newlines  "
        
        # Act
        result = normalize_whitespace(messy_text)
        
        # Assert
        assert result == "Multiple spaces and newlines"


class TestNumberProcessing:
    """測試數值處理"""
    
    @pytest.mark.unit
    def test_u007_clamp_value(self):
        """U-007: 數值限制範圍"""
        def clamp(value: float, min_val: float, max_val: float) -> float:
            return max(min_val, min(max_val, value))
        
        # Act & Assert
        assert clamp(5, 0, 10) == 5
        assert clamp(-1, 0, 10) == 0
        assert clamp(15, 0, 10) == 10
        assert clamp(7.5, 0, 10) == 7.5
    
    @pytest.mark.unit
    def test_u008_normalize_score(self):
        """U-008: 分數歸一化"""
        def normalize(value: float, old_min: float, old_max: float, 
                     new_min: float = 0.0, new_max: float = 1.0) -> float:
            if old_max == old_min:
                return new_min
            normalized = (value - old_min) / (old_max - old_min)
            return new_min + normalized * (new_max - new_min)
        
        # Arrange - 將 0-10 分數轉為 0-1
        score = 7.5
        
        # Act
        result = normalize(score, 0, 10, 0, 1)
        
        # Assert
        assert abs(result - 0.75) < 1e-6
        
        # Edge case
        same_range = normalize(5, 5, 5, 0, 1)
        assert same_range == 0.0


class TestDataValidation:
    """測試數據驗證"""
    
    @pytest.mark.unit
    def test_u009_validate_tmdb_id(self):
        """U-009: 驗證 TMDB ID"""
        def is_valid_tmdb_id(tmdb_id: int) -> bool:
            return isinstance(tmdb_id, int) and tmdb_id > 0
        
        # Act & Assert
        assert is_valid_tmdb_id(550) is True
        assert is_valid_tmdb_id(1) is True
        assert is_valid_tmdb_id(0) is False
        assert is_valid_tmdb_id(-1) is False
    
    @pytest.mark.unit
    def test_u010_validate_embedding_vector(self):
        """U-010: 驗證 Embedding 向量"""
        def is_valid_embedding(embedding: List[float], expected_dim: int = 1536) -> bool:
            if not isinstance(embedding, list):
                return False
            if len(embedding) != expected_dim:
                return False
            return all(isinstance(x, (int, float)) for x in embedding)
        
        # Arrange
        valid_embedding = [0.1] * 1536
        invalid_dim = [0.1] * 100
        invalid_type = ["0.1"] * 1536
        
        # Act & Assert
        assert is_valid_embedding(valid_embedding) is True
        assert is_valid_embedding(invalid_dim) is False
        assert is_valid_embedding(invalid_type) is False
        assert is_valid_embedding(None) is False


class TestMathUtilities:
    """測試數學工具函數"""
    
    @pytest.mark.unit
    def test_weighted_average(self):
        """測試加權平均"""
        def weighted_average(values: List[float], weights: List[float]) -> float:
            if not values or not weights or len(values) != len(weights):
                return 0.0
            total_weight = sum(weights)
            if total_weight == 0:
                return 0.0
            return sum(v * w for v, w in zip(values, weights)) / total_weight
        
        # Arrange
        values = [0.8, 0.6, 0.9]
        weights = [0.5, 0.3, 0.2]
        
        # Act
        result = weighted_average(values, weights)
        
        # Assert
        expected = (0.8 * 0.5 + 0.6 * 0.3 + 0.9 * 0.2) / (0.5 + 0.3 + 0.2)
        assert abs(result - expected) < 1e-6
