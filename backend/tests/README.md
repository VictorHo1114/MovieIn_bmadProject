# 推薦系統測試套件
**Recommendation System Test Suite**

## 📁 測試架構

```
tests/
├── __init__.py              # 測試套件初始化
├── conftest.py             # 共用 fixtures 與配置
│
├── unit/                   # 單元測試（50 個）
│   ├── test_embedding_service.py
│   ├── test_query_generator.py
│   ├── test_mood_analyzer.py
│   ├── test_recommendation_cache.py
│   ├── test_config_validation.py
│   └── test_utilities.py
│
├── integration/            # 整合測試（15 個）
│   ├── test_recommend_pipeline.py
│   ├── test_cache_integration.py
│   ├── test_db_operations.py
│   └── test_quadrant_workflow.py
│
├── e2e/                    # 端到端測試（10 個）
│   ├── test_recommendation_scenarios.py
│   └── test_api_endpoints.py
│
├── fixtures/               # 測試數據
│   ├── sample_movies.json
│   ├── sample_embeddings.json
│   └── test_queries.json
│
└── performance/            # 性能測試
    ├── test_embedding_cache_perf.py
    └── test_recommendation_latency.py
```

## 🚀 快速開始

### 1. 安裝依賴

```powershell
# 已安裝完成 ✅
pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist httpx freezegun
```

### 2. 執行所有測試

```powershell
# 在 backend 目錄下執行
cd backend
pytest
```

### 3. 執行特定層級測試

```powershell
# 單元測試（快速）
pytest tests/unit -v

# 整合測試
pytest tests/integration -v

# E2E 測試
pytest tests/e2e -v
```

### 4. 生成覆蓋率報告

```powershell
# 生成 HTML 報告
pytest --cov=app/services --cov-report=html

# 查看報告
start htmlcov/index.html
```

### 5. 執行特定測試文件

```powershell
# 測試 Embedding Service
pytest tests/unit/test_embedding_service.py -v

# 測試 Query Generator
pytest tests/unit/test_query_generator.py -v
```

### 6. 執行特定測試函數

```powershell
pytest tests/unit/test_embedding_service.py::TestGetEmbedding::test_get_embedding_normal_text -v
```

## 🔧 配置文件

### pytest.ini
- 測試發現配置
- 執行選項
- 測試標記定義

### .coveragerc
- 覆蓋率配置
- 排除規則
- 報告格式

### conftest.py
- 共用 fixtures
- 測試數據
- Mock 物件

## 📊 測試標記

使用 `-m` 選項執行特定標記的測試：

```powershell
# 只執行單元測試
pytest -m unit

# 只執行整合測試
pytest -m integration

# 只執行需要資料庫的測試
pytest -m db

# 排除耗時測試
pytest -m "not slow"
```

## 🎯 覆蓋率目標

| 模組 | 目標覆蓋率 | 當前狀態 |
|------|------------|---------|
| `simple_recommend.py` | 85%+ | 🔴 0% |
| `embedding_service.py` | 90%+ | 🔴 0% |
| `embedding_query_generator.py` | 90%+ | 🔴 0% |
| `mood_analyzer.py` | 85%+ | 🔴 0% |
| `recommendation_cache.py` | 80%+ | 🔴 0% |
| `phase36_config.py` | 100% | 🔴 0% |
| **總體** | **80%+** | **🔴 0%** |

## 📝 測試編寫指南

### AAA 模式

```python
def test_example():
    # Arrange - 準備測試數據
    movie = {"title": "Test Movie", "match_ratio": 0.5}
    
    # Act - 執行測試操作
    result = calculate_match_ratio(movie, ...)
    
    # Assert - 驗證結果
    assert result == expected_value
```

### 使用 Fixtures

```python
def test_with_fixtures(sample_movies, db_session):
    # 使用共用的測試數據和資料庫 session
    results = query_movies(db_session, sample_movies[0]["id"])
    assert len(results) > 0
```

### Mock 外部依賴

```python
@patch('app.services.embedding_service.client.embeddings.create')
def test_with_mock(mock_create):
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1] * 1536)]
    mock_create.return_value = mock_response
    
    result = get_embedding("test text", use_cache=False)
    assert len(result) == 1536
```

## 🐛 故障排除

### 找不到模組

```powershell
# 確保在 backend 目錄下執行
cd backend
pytest
```

### 資料庫連線問題

```powershell
# 使用內存資料庫（預設）
pytest

# 使用真實資料庫
pytest --use-real-db
```

### 快取問題

測試自動使用隔離的快取，每個測試後會清除。

## 📚 相關文檔

- [測試架構文檔](../docs/recommendation-system-unit-testing-architecture.md)
- [測試案例總覽](../docs/recommendation-system-test-cases-summary.md)
- [pytest 官方文檔](https://docs.pytest.org/)

## ✅ Phase 1 完成清單

- [x] 創建測試目錄結構
- [x] 設定 pytest 配置 (`pytest.ini`)
- [x] 設定 coverage 配置 (`.coveragerc`)
- [x] 實作共用 fixtures (`conftest.py`)
- [x] 創建測試數據 (`fixtures/*.json`)
- [x] 安裝測試依賴套件

## 🎯 下一步：Phase 2

開始實作單元測試（50 個測試案例）：
1. Embedding Service (E-001 ~ E-010)
2. Query Generator (Q-001 ~ Q-009)
3. Mood Analyzer (M-001 ~ M-009)
4. Cache System (C-001 ~ C-008)
5. Config Validation (V-001 ~ V-004)
6. Utilities (U-001 ~ U-010)

---

*Generated: 2025-12-12*  
*Status: Phase 1 完成 ✅*
