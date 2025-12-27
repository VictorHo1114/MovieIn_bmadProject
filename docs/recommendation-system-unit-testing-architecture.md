# 推薦系統單元測試架構文檔
**Recommendation System Unit Testing Architecture**

---

## 📋 文檔資訊

| 項目 | 內容 |
|------|------|
| **文檔版本** | v1.0 |
| **建立日期** | 2025-12-11 |
| **作者** | Winston (Architect) |
| **專案** | MovieIn BMAD Project |
| **系統版本** | Phase 3.6 Embedding-First |
| **測試框架** | pytest |
| **目標** | 達成 80%+ 代碼覆蓋率 |

---

## 🎯 測試目標與範圍

### 核心目標
1. **功能正確性驗證** - 確保每個組件按預期工作
2. **回歸測試保護** - 防止功能修改時引入 bug
3. **性能基準建立** - 監控關鍵路徑的性能指標
4. **邊界條件覆蓋** - 測試極端情況和錯誤處理
5. **整合點驗證** - 確保組件間協作正確

### 測試範圍
- ✅ **核心推薦引擎** (`simple_recommend.py`)
- ✅ **Embedding 服務** (`embedding_service.py`)
- ✅ **查詢生成器** (`embedding_query_generator.py`)
- ✅ **Mood 分析器** (`mood_analyzer.py`)
- ✅ **快取系統** (`recommendation_cache.py`)
- ✅ **配置管理** (`phase36_config.py`)
- ✅ **映射表** (`mapping_tables.py`)

### 不包含範圍
- ❌ Router 層（屬於 API 整合測試）
- ❌ 資料庫模型（屬於 DB 層測試）
- ❌ 前端整合（屬於 E2E 測試）

---

## 🏗️ 測試架構設計

### 三層測試金字塔

```
        /\
       /  \        E2E Tests (5-10%)
      /____\       - 完整流程測試
     /      \      - API 端點測試
    /________\     
   /          \    Integration Tests (20-30%)
  /____________\   - 組件協作測試
 /              \  - 資料庫整合測試
/________________\ 
                   Unit Tests (60-75%)
                   - 函數級別測試
                   - 純邏輯測試
```

### 測試檔案組織結構

```
backend/
├── tests/                          # 新建測試目錄
│   ├── __init__.py
│   ├── conftest.py                # pytest 配置與共用 fixtures
│   │
│   ├── unit/                      # 單元測試（Level 1）
│   │   ├── __init__.py
│   │   ├── test_embedding_service.py
│   │   ├── test_query_generator.py
│   │   ├── test_mood_analyzer.py
│   │   ├── test_recommendation_cache.py
│   │   ├── test_config_validation.py
│   │   └── test_utilities.py
│   │
│   ├── integration/               # 整合測試（Level 2）
│   │   ├── __init__.py
│   │   ├── test_recommend_pipeline.py
│   │   ├── test_cache_integration.py
│   │   ├── test_db_operations.py
│   │   └── test_quadrant_workflow.py
│   │
│   ├── e2e/                       # 端到端測試（Level 3）
│   │   ├── __init__.py
│   │   ├── test_recommendation_scenarios.py
│   │   └── test_api_endpoints.py
│   │
│   ├── fixtures/                  # 測試數據與 Fixtures
│   │   ├── __init__.py
│   │   ├── sample_movies.json
│   │   ├── sample_embeddings.json
│   │   └── test_queries.json
│   │
│   └── performance/               # 性能測試
│       ├── __init__.py
│       ├── test_embedding_cache_perf.py
│       └── test_recommendation_latency.py
│
├── app/
│   └── services/
│       ├── simple_recommend.py
│       ├── embedding_service.py
│       └── ...
│
├── test_cache_p0.py              # 保留（既有快取測試）
├── test_p1_performance.py        # 保留（既有性能測試）
└── test_diversity.py             # 保留（既有多樣性測試）
```

---

## 📦 Level 1: 單元測試（Unit Tests）

### 1.1 Embedding Service 測試
**檔案**: `tests/unit/test_embedding_service.py`

#### 測試範圍
```python
# backend/app/services/embedding_service.py

✓ get_embedding()               # 向量生成
✓ cosine_similarity()          # 相似度計算
✓ store_movie_embedding()      # 儲存向量
✓ batch_calculate_embeddings() # 批次計算
```

#### 測試案例設計

| 測試 ID | 測試名稱 | 測試目的 | 預期結果 |
|---------|----------|----------|----------|
| **E-001** | `test_get_embedding_normal_text` | 測試正常文本向量生成 | 返回 1536 維向量 |
| **E-002** | `test_get_embedding_empty_text` | 測試空文本處理 | 返回零向量 [0.0] * 1536 |
| **E-003** | `test_get_embedding_chinese_text` | 測試中文文本 | 正確生成向量 |
| **E-004** | `test_get_embedding_long_text` | 測試長文本（>8192 tokens） | 截斷並生成向量 |
| **E-005** | `test_get_embedding_with_cache` | 測試快取啟用 | 第二次呼叫命中快取 |
| **E-006** | `test_get_embedding_cache_disabled` | 測試快取停用 | 每次都呼叫 API |
| **E-007** | `test_cosine_similarity_identical` | 測試相同向量相似度 | 返回 1.0 |
| **E-008** | `test_cosine_similarity_orthogonal` | 測試正交向量相似度 | 返回 ~0.0 |
| **E-009** | `test_cosine_similarity_zero_vector` | 測試零向量處理 | 返回 0.0（不拋錯） |
| **E-010** | `test_store_embedding_success` | 測試儲存成功 | DB 中有記錄 |

#### 實作範例

```python
# tests/unit/test_embedding_service.py
import pytest
import numpy as np
from unittest.mock import Mock, patch
from app.services.embedding_service import (
    get_embedding,
    cosine_similarity,
    store_movie_embedding
)

class TestGetEmbedding:
    """測試 get_embedding() 函數"""
    
    @patch('app.services.embedding_service.client.embeddings.create')
    def test_get_embedding_normal_text(self, mock_create):
        """E-001: 測試正常文本向量生成"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_create.return_value = mock_response
        
        # Act
        result = get_embedding("A heartwarming family movie", use_cache=False)
        
        # Assert
        assert len(result) == 1536
        assert isinstance(result[0], float)
        mock_create.assert_called_once()
    
    def test_get_embedding_empty_text(self):
        """E-002: 測試空文本處理"""
        # Act
        result = get_embedding("", use_cache=False)
        
        # Assert
        assert len(result) == 1536
        assert all(v == 0.0 for v in result)
    
    @patch('app.services.embedding_service.client.embeddings.create')
    def test_get_embedding_with_cache(self, mock_create):
        """E-005: 測試快取啟用"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.2] * 1536)]
        mock_create.return_value = mock_response
        text = "Test cache functionality"
        
        # Act - 第一次呼叫
        result1 = get_embedding(text, use_cache=True)
        # Act - 第二次呼叫（應該命中快取）
        result2 = get_embedding(text, use_cache=True)
        
        # Assert
        assert result1 == result2
        assert mock_create.call_count == 1  # 只呼叫一次 API

class TestCosineSimilarity:
    """測試 cosine_similarity() 函數"""
    
    def test_cosine_similarity_identical(self):
        """E-007: 測試相同向量相似度"""
        # Arrange
        vec = [0.5] * 1536
        
        # Act
        similarity = cosine_similarity(vec, vec)
        
        # Assert
        assert pytest.approx(similarity, abs=1e-6) == 1.0
    
    def test_cosine_similarity_orthogonal(self):
        """E-008: 測試正交向量相似度"""
        # Arrange
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        
        # Act
        similarity = cosine_similarity(vec1, vec2)
        
        # Assert
        assert pytest.approx(similarity, abs=1e-6) == 0.0
    
    def test_cosine_similarity_zero_vector(self):
        """E-009: 測試零向量處理"""
        # Arrange
        vec1 = [0.0] * 1536
        vec2 = [0.5] * 1536
        
        # Act
        similarity = cosine_similarity(vec1, vec2)
        
        # Assert
        assert similarity == 0.0  # 不拋錯，返回 0
```

---

### 1.2 Query Generator 測試
**檔案**: `tests/unit/test_query_generator.py`

#### 測試範圍
```python
# backend/app/services/embedding_query_generator.py

✓ generate_embedding_query()    # 主查詢生成函數
✓ detect_sentiment_conflict()  # 情感衝突檢測
✓ _scenario_nl_only()          # 僅自然語言
✓ _scenario_mood_only()        # 僅 Mood 標籤
✓ _scenario_both()             # 兩者皆有
```

#### 測試案例設計

| 測試 ID | 測試名稱 | 測試目的 | 預期結果 |
|---------|----------|----------|----------|
| **Q-001** | `test_scenario_nl_only` | 測試僅自然語言輸入 | scenario="nl_only" |
| **Q-002** | `test_scenario_mood_only` | 測試僅 Mood 輸入 | scenario="mood_only", 生成 template |
| **Q-003** | `test_scenario_both_no_conflict` | 測試 NL + Mood 無衝突 | scenario="both", conflict=False |
| **Q-004** | `test_scenario_both_with_conflict` | 測試 NL + Mood 有衝突 | conflict=True, 警告提示 |
| **Q-005** | `test_empty_input` | 測試空輸入 | scenario="empty" |
| **Q-006** | `test_mood_relationship_journey` | 測試 Journey 關係 | type="journey" |
| **Q-007** | `test_mood_relationship_paradox` | 測試 Paradox 關係 | type="paradox" |
| **Q-008** | `test_chinese_natural_query` | 測試中文查詢 | 正確處理 |
| **Q-009** | `test_multiple_mood_labels` | 測試多個 Mood | 正確分析關係 |

#### 實作範例

```python
# tests/unit/test_query_generator.py
import pytest
from app.services.embedding_query_generator import (
    generate_embedding_query,
    detect_sentiment_conflict
)

class TestGenerateEmbeddingQuery:
    """測試 generate_embedding_query() 函數"""
    
    def test_scenario_nl_only(self):
        """Q-001: 測試僅自然語言輸入"""
        # Arrange
        natural_query = "難過的時候適合看什麼電影"
        mood_labels = []
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["scenario"] == "nl_only"
        assert result["query"] == natural_query
        assert result["mood_relationship"] is None
        assert result["conflict_detected"] is False
    
    def test_scenario_mood_only(self):
        """Q-002: 測試僅 Mood 輸入"""
        # Arrange
        natural_query = None
        mood_labels = ["emotional", "heartwarming"]
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["scenario"] == "mood_only"
        assert "heartwarming" in result["query"].lower()
        assert result["mood_relationship"] is not None
        assert result["mood_relationship"]["type"] == "journey"
    
    def test_scenario_both_no_conflict(self):
        """Q-003: 測試 NL + Mood 無衝突"""
        # Arrange
        natural_query = "想看溫馨感人的電影"
        mood_labels = ["heartwarming", "uplifting"]
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["scenario"] == "both"
        assert result["query"] == natural_query  # NL 優先
        assert result["conflict_detected"] is False
    
    def test_scenario_both_with_conflict(self):
        """Q-004: 測試 NL + Mood 有衝突"""
        # Arrange
        natural_query = "想看歡樂有趣的電影"  # 歡樂
        mood_labels = ["dark", "gritty"]        # 黑暗
        
        # Act
        result = generate_embedding_query(natural_query, mood_labels)
        
        # Assert
        assert result["conflict_detected"] is True
    
    def test_empty_input(self):
        """Q-005: 測試空輸入"""
        # Act
        result = generate_embedding_query(None, [])
        
        # Assert
        assert result["scenario"] == "empty"
        assert result["query"] == ""

class TestSentimentConflict:
    """測試 detect_sentiment_conflict() 函數"""
    
    def test_no_conflict_positive(self):
        """測試正面情緒無衝突"""
        assert not detect_sentiment_conflict("happy movie", ["cheerful", "uplifting"])
    
    def test_conflict_positive_vs_negative(self):
        """測試正負情緒衝突"""
        assert detect_sentiment_conflict("happy movie", ["dark", "melancholic"])
```

---

### 1.3 Mood Analyzer 測試
**檔案**: `tests/unit/test_mood_analyzer.py`

#### 測試範圍
```python
# backend/app/services/mood_analyzer.py

✓ analyze_mood_combination()   # 主分析函數
✓ _generate_template()         # 模板生成
✓ MOOD_RELATIONSHIP_MATRIX     # 關係矩陣驗證
```

#### 測試案例設計

| 測試 ID | 測試名稱 | 測試目的 | 預期結果 |
|---------|----------|----------|----------|
| **M-001** | `test_journey_relationship` | 測試 Journey 關係 | 正確識別轉變關係 |
| **M-002** | `test_paradox_relationship` | 測試 Paradox 關係 | 正確識別矛盾關係 |
| **M-003** | `test_intensification_relationship` | 測試 Intensification | 正確識別強化關係 |
| **M-004** | `test_multi_faceted_relationship` | 測試 Multi-faceted | 正確識別多面關係 |
| **M-005** | `test_unknown_combination` | 測試未知組合 | 返回通用模板 |
| **M-006** | `test_single_mood` | 測試單一 Mood | 返回簡單模板 |
| **M-007** | `test_three_moods` | 測試三個 Mood | 優先處理前兩個 |
| **M-008** | `test_mood_order_independence` | 測試順序無關性 | (A,B) == (B,A) |
| **M-009** | `test_matrix_completeness` | 驗證關係矩陣完整性 | 51 對關係都存在 |

#### 實作範例

```python
# tests/unit/test_mood_analyzer.py
import pytest
from app.services.mood_analyzer import (
    analyze_mood_combination,
    MOOD_RELATIONSHIP_MATRIX
)

class TestMoodCombination:
    """測試 analyze_mood_combination() 函數"""
    
    def test_journey_relationship(self):
        """M-001: 測試 Journey 關係"""
        # Arrange
        moods = ["emotional", "heartwarming"]
        
        # Act
        result = analyze_mood_combination(moods)
        
        # Assert
        assert result["type"] == "journey"
        assert "emotional healing" in result["template"].lower()
        assert result["confidence"] == "high"
        assert result["source"] == "matrix"
    
    def test_paradox_relationship(self):
        """M-002: 測試 Paradox 關係"""
        # Arrange
        moods = ["dark", "lighthearted"]
        
        # Act
        result = analyze_mood_combination(moods)
        
        # Assert
        assert result["type"] == "paradox"
        assert "dark comedy" in result["template"].lower()
    
    def test_unknown_combination(self):
        """M-005: 測試未知組合"""
        # Arrange
        moods = ["unknown_mood_1", "unknown_mood_2"]
        
        # Act
        result = analyze_mood_combination(moods)
        
        # Assert
        assert result["type"] == "multi-faceted"
        assert result["confidence"] == "medium"
        assert result["source"] == "fallback"
    
    def test_mood_order_independence(self):
        """M-008: 測試順序無關性"""
        # Act
        result1 = analyze_mood_combination(["emotional", "heartwarming"])
        result2 = analyze_mood_combination(["heartwarming", "emotional"])
        
        # Assert
        assert result1["type"] == result2["type"]
        assert result1["template"] == result2["template"]

class TestRelationshipMatrix:
    """驗證 MOOD_RELATIONSHIP_MATRIX 資料品質"""
    
    def test_matrix_completeness(self):
        """M-009: 驗證關係矩陣完整性"""
        # 應該包含 51 對關係
        assert len(MOOD_RELATIONSHIP_MATRIX) >= 51
    
    def test_all_entries_have_required_fields(self):
        """驗證所有條目都有必要欄位"""
        required_fields = ["type", "description", "template"]
        
        for key, value in MOOD_RELATIONSHIP_MATRIX.items():
            for field in required_fields:
                assert field in value, f"Missing {field} in {key}"
```

---

### 1.4 Recommendation Cache 測試
**檔案**: `tests/unit/test_recommendation_cache.py`

#### 測試範圍
```python
# backend/app/services/recommendation_cache.py

✓ get_cached_embedding()
✓ set_cached_embedding()
✓ get_cached_recommendation()
✓ set_cached_recommendation()
✓ generate_recommendation_cache_key()
✓ invalidate_recommendation_cache()
✓ get_cache_stats()
```

#### 測試案例設計

| 測試 ID | 測試名稱 | 測試目的 | 預期結果 |
|---------|----------|----------|----------|
| **C-001** | `test_embedding_cache_miss` | 測試快取未命中 | 返回 None |
| **C-002** | `test_embedding_cache_hit` | 測試快取命中 | 返回正確向量 |
| **C-003** | `test_embedding_cache_ttl` | 測試 TTL 過期 | 過期後返回 None |
| **C-004** | `test_recommendation_cache_key_generation` | 測試鍵生成 | 參數順序不影響 |
| **C-005** | `test_recommendation_cache_hit` | 測試推薦快取命中 | 返回正確結果 |
| **C-006** | `test_cache_invalidation` | 測試快取失效 | 正確清除 |
| **C-007** | `test_cache_stats` | 測試統計資訊 | 正確計數 |
| **C-008** | `test_redis_fallback` | 測試 Redis 降級 | LRU Cache 仍可用 |

#### 實作範例

```python
# tests/unit/test_recommendation_cache.py
import pytest
from app.services.recommendation_cache import (
    get_cached_embedding,
    set_cached_embedding,
    get_cached_recommendation,
    set_cached_recommendation,
    generate_recommendation_cache_key,
    invalidate_recommendation_cache
)

class TestEmbeddingCache:
    """測試 Embedding 快取"""
    
    def test_embedding_cache_miss(self):
        """C-001: 測試快取未命中"""
        # Arrange
        invalidate_recommendation_cache()
        
        # Act
        result = get_cached_embedding("new text")
        
        # Assert
        assert result is None
    
    def test_embedding_cache_hit(self):
        """C-002: 測試快取命中"""
        # Arrange
        text = "test embedding cache"
        embedding = [0.5] * 1536
        set_cached_embedding(text, embedding)
        
        # Act
        result = get_cached_embedding(text)
        
        # Assert
        assert result == embedding

class TestRecommendationCache:
    """測試推薦結果快取"""
    
    def test_recommendation_cache_key_generation(self):
        """C-004: 測試鍵生成"""
        # Act - 參數順序不同
        key1 = generate_recommendation_cache_key(
            natural_query="test",
            mood_labels=["happy", "uplifting"],
            genres=["Drama"]
        )
        key2 = generate_recommendation_cache_key(
            natural_query="test",
            mood_labels=["uplifting", "happy"],  # 順序不同
            genres=["Drama"]
        )
        
        # Assert - 應該生成相同的鍵
        assert key1 == key2
    
    def test_cache_invalidation(self):
        """C-006: 測試快取失效"""
        # Arrange
        set_cached_recommendation(
            result=[{"id": 1, "title": "Test"}],
            natural_query="test",
            mood_labels=[],
            genres=[]
        )
        
        # Act
        invalidate_recommendation_cache()
        result = get_cached_recommendation("test", [], [])
        
        # Assert
        assert result is None
```

---

### 1.5 Config Validation 測試
**檔案**: `tests/unit/test_config_validation.py`

#### 測試範圍
```python
# backend/app/services/phase36_config.py

✓ PHASE36_CONFIG 完整性驗證
✓ 權重總和驗證（應為 1.0）
✓ 閾值範圍驗證（0-1）
✓ 候選數量邏輯驗證
```

#### 測試案例設計

| 測試 ID | 測試名稱 | 測試目的 | 預期結果 |
|---------|----------|----------|----------|
| **V-001** | `test_config_structure_complete` | 驗證配置結構完整 | 所有必要鍵存在 |
| **V-002** | `test_quadrant_weights_sum_to_one` | 驗證權重總和 | 每個象限權重 = 1.0 |
| **V-003** | `test_thresholds_in_valid_range` | 驗證閾值範圍 | 0 ≤ threshold ≤ 1 |
| **V-004** | `test_candidate_counts_logic` | 驗證候選數邏輯 | top_k > filter_k > final |

#### 實作範例

```python
# tests/unit/test_config_validation.py
import pytest
from app.services.phase36_config import PHASE36_CONFIG

class TestConfigValidation:
    """驗證 Phase 3.6 配置正確性"""
    
    def test_quadrant_weights_sum_to_one(self):
        """V-002: 驗證權重總和為 1.0"""
        weights = PHASE36_CONFIG["quadrant_weights"]
        
        for quadrant, w in weights.items():
            total = w["embedding"] + w["feature"] + w["match_ratio"]
            assert pytest.approx(total, abs=1e-6) == 1.0, \
                f"{quadrant} weights don't sum to 1.0: {total}"
    
    def test_thresholds_in_valid_range(self):
        """V-003: 驗證閾值範圍"""
        thresholds = PHASE36_CONFIG["quadrant_thresholds"]
        
        for name, value in thresholds.items():
            assert 0 <= value <= 1, \
                f"Threshold {name}={value} out of range [0, 1]"
    
    def test_candidate_counts_logic(self):
        """V-004: 驗證候選數邏輯"""
        counts = PHASE36_CONFIG["candidate_counts"]
        
        assert counts["embedding_top_k"] >= counts["feature_filter_k"]
        assert counts["feature_filter_k"] >= counts["final_recommendations"]
```

---

### 1.6 Utilities 測試
**檔案**: `tests/unit/test_utilities.py`

#### 測試範圍
```python
# backend/app/services/simple_recommend.py - Utility Functions

✓ calculate_match_ratio()
✓ classify_to_3quadrant()
✓ calculate_3quadrant_score()
✓ _check_year_in_range()
```

#### 測試案例設計

| 測試 ID | 測試名稱 | 測試目的 | 預期結果 |
|---------|----------|----------|----------|
| **U-001** | `test_match_ratio_perfect_match` | 測試完美匹配 | ratio = 1.0 |
| **U-002** | `test_match_ratio_partial_match` | 測試部分匹配 | 0 < ratio < 1 |
| **U-003** | `test_match_ratio_no_match` | 測試無匹配 | ratio = 0.0 |
| **U-004** | `test_match_ratio_no_requirements` | 測試無要求 | ratio = 1.0 |
| **U-005** | `test_classify_q1_perfect` | 測試 Q1 分類 | quadrant = "q1_perfect_match" |
| **U-006** | `test_classify_q2_discovery` | 測試 Q2 分類 | quadrant = "q2_semantic_discovery" |
| **U-007** | `test_classify_q4_fallback` | 測試 Q4 分類 | quadrant = "q4_fallback" |
| **U-008** | `test_score_calculation_q1` | 測試 Q1 評分 | 使用平衡權重 |
| **U-009** | `test_year_range_check_valid` | 測試年份範圍（有效） | 返回 True |
| **U-010** | `test_year_range_check_invalid` | 測試年份範圍（無效） | 返回 False |

#### 實作範例

```python
# tests/unit/test_utilities.py
import pytest
from app.services.simple_recommend import (
    calculate_match_ratio,
    classify_to_3quadrant,
    calculate_3quadrant_score,
    _check_year_in_range
)

class TestMatchRatio:
    """測試 calculate_match_ratio() 函數"""
    
    def test_match_ratio_perfect_match(self):
        """U-001: 測試完美匹配"""
        # Arrange
        movie = {
            "keywords": ["love", "family"],
            "mood_tags": ["heartwarming"],
            "genres": ["剧情"]
        }
        keywords = ["love", "family"]
        mood_tags = ["heartwarming"]
        genres = ["Drama"]  # 會轉換為 "剧情"
        
        # Act
        ratio = calculate_match_ratio(movie, keywords, mood_tags, genres)
        
        # Assert
        assert pytest.approx(ratio, abs=1e-6) == 1.0
    
    def test_match_ratio_partial_match(self):
        """U-002: 測試部分匹配"""
        # Arrange
        movie = {
            "keywords": ["love"],  # 只有 1/2
            "mood_tags": [],       # 0/1
            "genres": ["剧情"]     # 1/1
        }
        
        # Act
        ratio = calculate_match_ratio(
            movie,
            keywords=["love", "family"],
            mood_tags=["heartwarming"],
            genres=["Drama"]
        )
        
        # Assert
        # 符合: 2/4 = 0.5
        assert pytest.approx(ratio, abs=1e-6) == 0.5

class TestQuadrantClassification:
    """測試三象限分類"""
    
    def test_classify_q1_perfect(self):
        """U-005: 測試 Q1 分類"""
        # Arrange
        movie = {"match_ratio": 0.75}  # High match (>0.40)
        embedding_score = 0.70          # High embedding (>0.60)
        
        # Act
        quadrant = classify_to_3quadrant(movie, embedding_score)
        
        # Assert
        assert quadrant == "q1_perfect_match"
    
    def test_classify_q2_discovery(self):
        """U-006: 測試 Q2 分類"""
        # Arrange
        movie = {"match_ratio": 0.30}  # Low match (<0.40)
        embedding_score = 0.70          # High embedding (>0.60)
        
        # Act
        quadrant = classify_to_3quadrant(movie, embedding_score)
        
        # Assert
        assert quadrant == "q2_semantic_discovery"
    
    def test_classify_q4_fallback(self):
        """U-007: 測試 Q4 分類"""
        # Arrange
        movie = {"match_ratio": 0.80}  # High match
        embedding_score = 0.50          # Low embedding (<0.60)
        
        # Act
        quadrant = classify_to_3quadrant(movie, embedding_score)
        
        # Assert
        assert quadrant == "q4_fallback"

class TestYearRange:
    """測試年份範圍檢查"""
    
    def test_year_range_check_valid(self):
        """U-009: 測試年份範圍（有效）"""
        assert _check_year_in_range("1995-06-15", 1990, 2000) is True
    
    def test_year_range_check_invalid(self):
        """U-010: 測試年份範圍（無效）"""
        assert _check_year_in_range("2020-01-01", 1990, 2000) is False
```

---

## 📦 Level 2: 整合測試（Integration Tests）

### 2.1 Recommendation Pipeline 測試
**檔案**: `tests/integration/test_recommend_pipeline.py`

#### 測試範圍
完整推薦流程（7 個步驟）整合測試

#### 測試案例設計

| 測試 ID | 測試名稱 | 測試目的 | 預期結果 |
|---------|----------|----------|----------|
| **I-001** | `test_full_pipeline_nl_only` | 測試完整流程（僅 NL） | 返回 10 部電影 |
| **I-002** | `test_full_pipeline_mood_only` | 測試完整流程（僅 Mood） | 返回推薦 + 象限分佈 |
| **I-003** | `test_full_pipeline_with_filters` | 測試帶過濾條件 | 正確應用過濾 |
| **I-004** | `test_pipeline_quadrant_distribution` | 測試象限分佈 | Q1 > Q2 > Q4 |
| **I-005** | `test_pipeline_with_cache` | 測試快取整合 | 第二次查詢命中快取 |

#### 實作範例

```python
# tests/integration/test_recommend_pipeline.py
import pytest
from app.services.simple_recommend import recommend_movies_embedding_first
from db.database import SessionLocal

class TestRecommendationPipeline:
    """測試完整推薦流程"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_nl_only(self, db_session):
        """I-001: 測試完整流程（僅自然語言）"""
        # Act
        results = await recommend_movies_embedding_first(
            natural_query="A heartwarming family movie",
            mood_labels=[],
            genres=[],
            db_session=db_session,
            count=10
        )
        
        # Assert
        assert len(results) <= 10
        assert all("title" in movie for movie in results)
        assert all("quadrant" in movie for movie in results)
        assert all("final_score" in movie for movie in results)
    
    @pytest.mark.asyncio
    async def test_pipeline_quadrant_distribution(self, db_session):
        """I-004: 測試象限分佈"""
        # Act
        results = await recommend_movies_embedding_first(
            natural_query="emotional healing",
            mood_labels=["heartwarming", "uplifting"],
            genres=["Drama"],
            db_session=db_session,
            count=50
        )
        
        # Assert - 統計象限分佈
        quadrants = [m["quadrant"] for m in results]
        q1_count = quadrants.count("q1_perfect_match")
        q2_count = quadrants.count("q2_semantic_discovery")
        q4_count = quadrants.count("q4_fallback")
        
        # Q1 應該最多（高質量推薦）
        assert q1_count >= q2_count
        assert q1_count >= q4_count
```

---

### 2.2 Cache Integration 測試
**檔案**: `tests/integration/test_cache_integration.py`

#### 測試案例設計

| 測試 ID | 測試名稱 | 測試目的 | 預期結果 |
|---------|----------|----------|----------|
| **CI-001** | `test_embedding_cache_reduces_api_calls` | 驗證快取減少 API 呼叫 | 第二次不呼叫 API |
| **CI-002** | `test_recommendation_cache_improves_latency` | 驗證快取提升效能 | 快取命中 < 10ms |
| **CI-003** | `test_cache_invalidation_workflow` | 測試快取失效流程 | 失效後重新計算 |

---

### 2.3 Database Operations 測試
**檔案**: `tests/integration/test_db_operations.py`

#### 測試範圍
- Embedding 向量搜索（pgvector）
- 過濾條件組合
- 排序邏輯

---

## 📦 Level 3: 端到端測試（E2E Tests）

### 3.1 Recommendation Scenarios 測試
**檔案**: `tests/e2e/test_recommendation_scenarios.py`

#### 測試場景

| 場景 ID | 場景名稱 | 描述 |
|---------|----------|------|
| **S-001** | Journey 情境 | "難過的時候適合看什麼" + heartwarming |
| **S-002** | Paradox 情境 | "dark comedy" |
| **S-003** | 多維過濾 | Genres + Eras + Moods |
| **S-004** | 邊界情況 | 極少候選 |

---

## 🧪 測試數據與 Fixtures

### Fixtures 設計
**檔案**: `tests/conftest.py`

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base

@pytest.fixture(scope="session")
def db_engine():
    """創建測試資料庫引擎"""
    engine = create_engine("postgresql://localhost/test_moviein")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """創建測試資料庫 Session"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_movies():
    """樣本電影數據"""
    return [
        {
            "id": 550,
            "title": "It's a Wonderful Life",
            "overview": "A heartwarming story...",
            "genres": ["剧情"],
            "mood_tags": ["heartwarming", "uplifting"],
            "keywords": ["family", "hope"],
            "vote_average": 8.5,
            "release_date": "1946-12-20"
        },
        # ... 更多樣本
    ]

@pytest.fixture
def sample_embeddings():
    """樣本向量數據"""
    return {
        "heartwarming story": [0.5] * 1536,
        "dark thriller": [0.3] * 1536,
    }
```

---

## 🔧 測試工具與配置

### pytest 配置
**檔案**: `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=app/services
    --cov-report=html
    --cov-report=term-missing
    --asyncio-mode=auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    db: Tests requiring database
```

### Coverage 配置
**檔案**: `.coveragerc`

```ini
[run]
source = app/services
omit =
    */tests/*
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## 📊 測試覆蓋率目標

| 模組 | 目標覆蓋率 | 優先級 |
|------|------------|--------|
| `simple_recommend.py` | 85%+ | P0 |
| `embedding_service.py` | 90%+ | P0 |
| `embedding_query_generator.py` | 90%+ | P0 |
| `mood_analyzer.py` | 85%+ | P1 |
| `recommendation_cache.py` | 80%+ | P1 |
| `phase36_config.py` | 100% | P2 |

**總體目標**: 80%+ 代碼覆蓋率

---

## 🚀 測試執行指令

### 執行所有測試
```powershell
pytest
```

### 執行單元測試
```powershell
pytest tests/unit -m unit
```

### 執行整合測試
```powershell
pytest tests/integration -m integration
```

### 生成覆蓋率報告
```powershell
pytest --cov=app/services --cov-report=html
# 報告位置: htmlcov/index.html
```

### 執行特定測試文件
```powershell
pytest tests/unit/test_embedding_service.py -v
```

### 執行特定測試函數
```powershell
pytest tests/unit/test_embedding_service.py::TestGetEmbedding::test_get_embedding_normal_text
```

---

## 📅 實施計劃

### Phase 1: 基礎建設（Week 1）
- [ ] 創建測試目錄結構
- [ ] 設定 pytest 配置
- [ ] 建立共用 fixtures
- [ ] 實作 `conftest.py`

### Phase 2: 單元測試（Week 2-3）
- [ ] Embedding Service 測試（E-001 ~ E-010）
- [ ] Query Generator 測試（Q-001 ~ Q-009）
- [ ] Mood Analyzer 測試（M-001 ~ M-009）
- [ ] Cache 測試（C-001 ~ C-008）
- [ ] Utilities 測試（U-001 ~ U-010）

### Phase 3: 整合測試（Week 4）
- [ ] Pipeline 測試（I-001 ~ I-005）
- [ ] Cache Integration 測試
- [ ] DB Operations 測試

### Phase 4: E2E 測試（Week 5）
- [ ] Scenario 測試（S-001 ~ S-004）
- [ ] API 端點測試

### Phase 5: 優化與維護（Ongoing）
- [ ] 達成 80%+ 覆蓋率
- [ ] 性能基準測試
- [ ] CI/CD 整合

---

## 🎓 最佳實踐

### 測試設計原則
1. **AAA 模式**: Arrange - Act - Assert
2. **獨立性**: 每個測試獨立運行
3. **可重複性**: 結果一致，不依賴外部狀態
4. **快速執行**: 單元測試 < 100ms
5. **清晰命名**: 測試名稱描述測試內容

### Mock 使用準則
- **Mock 外部依賴**: OpenAI API、Redis、Database
- **不 Mock 測試目標**: 測試的主函數不應被 Mock
- **使用 pytest-mock**: `mocker.patch()` 優於 `unittest.mock`

### 測試數據管理
- **使用 Fixtures**: 共用測試數據
- **避免硬編碼**: 使用配置文件或工廠函數
- **清理測試數據**: 每次測試後清理

---

## 📚 參考資源

- [pytest 官方文檔](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

## 📝 附錄：測試案例總覽

### 測試統計
- **單元測試**: 50+ 個測試案例
- **整合測試**: 15+ 個測試案例
- **E2E 測試**: 10+ 個測試案例
- **預計總測試數**: 75+ 個測試

### 測試 ID 索引
- **E-系列**: Embedding Service (E-001 ~ E-010)
- **Q-系列**: Query Generator (Q-001 ~ Q-009)
- **M-系列**: Mood Analyzer (M-001 ~ M-009)
- **C-系列**: Cache (C-001 ~ C-008)
- **V-系列**: Config Validation (V-001 ~ V-004)
- **U-系列**: Utilities (U-001 ~ U-010)
- **I-系列**: Integration (I-001 ~ I-005)
- **S-系列**: Scenarios (S-001 ~ S-004)

---

**文檔結束**

*Generated by Winston - Holistic System Architect*  
*Date: 2025-12-11*
