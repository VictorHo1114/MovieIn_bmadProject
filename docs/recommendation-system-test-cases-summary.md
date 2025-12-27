# 推薦系統測試案例整理表
**Recommendation System Test Cases Summary**

---

## 📊 總覽統計

| 測試類型 | 測試數量 | 優先級 | 預估時間 |
|---------|---------|--------|---------|
| **單元測試 (Unit Tests)** | 50 個 | P0-P1 | 2-3 週 |
| **整合測試 (Integration Tests)** | 15 個 | P1 | 1 週 |
| **端到端測試 (E2E Tests)** | 10 個 | P2 | 1 週 |
| **總計** | **75 個** | - | **5 週** |

**目標覆蓋率**: 80%+ 代碼覆蓋率

---

## 🧪 Level 1: 單元測試總表

### 📊 測試模組統計

| 模組 | 測試數量 | 測試 ID 範圍 | 檔案名稱 | 優先級 | 目標覆蓋率 |
|------|---------|-------------|---------|--------|-----------|
| Embedding Service | 10 | E-001 ~ E-010 | `test_embedding_service.py` | P0 | 90%+ |
| Query Generator | 9 | Q-001 ~ Q-009 | `test_query_generator.py` | P0 | 90%+ |
| Mood Analyzer | 9 | M-001 ~ M-009 | `test_mood_analyzer.py` | P1 | 85%+ |
| Cache System | 8 | C-001 ~ C-008 | `test_recommendation_cache.py` | P1 | 80%+ |
| Config Validation | 4 | V-001 ~ V-004 | `test_config_validation.py` | P2 | 100% |
| Utilities | 10 | U-001 ~ U-010 | `test_utilities.py` | P0 | 85%+ |
| **總計** | **50** | - | - | - | **85%+** |

---

## 📋 詳細測試案例清單

### 1️⃣ Embedding Service 測試 (E-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **E-001** | `test_get_embedding_normal_text` | 測試正常文本向量生成 | 返回 1536 維向量 | P0 |
| **E-002** | `test_get_embedding_empty_text` | 測試空文本處理 | 返回零向量 [0.0] * 1536 | P0 |
| **E-003** | `test_get_embedding_chinese_text` | 測試中文文本 | 正確生成向量 | P0 |
| **E-004** | `test_get_embedding_long_text` | 測試長文本（>8192 tokens） | 截斷並生成向量 | P1 |
| **E-005** | `test_get_embedding_with_cache` | 測試快取啟用 | 第二次呼叫命中快取 | P0 |
| **E-006** | `test_get_embedding_cache_disabled` | 測試快取停用 | 每次都呼叫 API | P1 |
| **E-007** | `test_cosine_similarity_identical` | 測試相同向量相似度 | 返回 1.0 | P0 |
| **E-008** | `test_cosine_similarity_orthogonal` | 測試正交向量相似度 | 返回 ~0.0 | P0 |
| **E-009** | `test_cosine_similarity_zero_vector` | 測試零向量處理 | 返回 0.0（不拋錯） | P1 |
| **E-010** | `test_store_embedding_success` | 測試儲存成功 | DB 中有記錄 | P1 |

---

### 2️⃣ Query Generator 測試 (Q-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **Q-001** | `test_scenario_nl_only` | 測試僅自然語言輸入 | scenario="nl_only" | P0 |
| **Q-002** | `test_scenario_mood_only` | 測試僅 Mood 輸入 | scenario="mood_only", 生成 template | P0 |
| **Q-003** | `test_scenario_both_no_conflict` | 測試 NL + Mood 無衝突 | scenario="both", conflict=False | P0 |
| **Q-004** | `test_scenario_both_with_conflict` | 測試 NL + Mood 有衝突 | conflict=True, 警告提示 | P1 |
| **Q-005** | `test_empty_input` | 測試空輸入 | scenario="empty" | P1 |
| **Q-006** | `test_mood_relationship_journey` | 測試 Journey 關係 | type="journey" | P0 |
| **Q-007** | `test_mood_relationship_paradox` | 測試 Paradox 關係 | type="paradox" | P1 |
| **Q-008** | `test_chinese_natural_query` | 測試中文查詢 | 正確處理 | P0 |
| **Q-009** | `test_multiple_mood_labels` | 測試多個 Mood | 正確分析關係 | P1 |

---

### 3️⃣ Mood Analyzer 測試 (M-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **M-001** | `test_journey_relationship` | 測試 Journey 關係 | 正確識別轉變關係 | P0 |
| **M-002** | `test_paradox_relationship` | 測試 Paradox 關係 | 正確識別矛盾關係 | P1 |
| **M-003** | `test_intensification_relationship` | 測試 Intensification | 正確識別強化關係 | P1 |
| **M-004** | `test_multi_faceted_relationship` | 測試 Multi-faceted | 正確識別多面關係 | P1 |
| **M-005** | `test_unknown_combination` | 測試未知組合 | 返回通用模板 | P1 |
| **M-006** | `test_single_mood` | 測試單一 Mood | 返回簡單模板 | P1 |
| **M-007** | `test_three_moods` | 測試三個 Mood | 優先處理前兩個 | P2 |
| **M-008** | `test_mood_order_independence` | 測試順序無關性 | (A,B) == (B,A) | P0 |
| **M-009** | `test_matrix_completeness` | 驗證關係矩陣完整性 | 51 對關係都存在 | P0 |

---

### 4️⃣ Cache System 測試 (C-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **C-001** | `test_embedding_cache_miss` | 測試快取未命中 | 返回 None | P0 |
| **C-002** | `test_embedding_cache_hit` | 測試快取命中 | 返回正確向量 | P0 |
| **C-003** | `test_embedding_cache_ttl` | 測試 TTL 過期 | 過期後返回 None | P1 |
| **C-004** | `test_recommendation_cache_key_generation` | 測試鍵生成 | 參數順序不影響 | P0 |
| **C-005** | `test_recommendation_cache_hit` | 測試推薦快取命中 | 返回正確結果 | P0 |
| **C-006** | `test_cache_invalidation` | 測試快取失效 | 正確清除 | P1 |
| **C-007** | `test_cache_stats` | 測試統計資訊 | 正確計數 | P1 |
| **C-008** | `test_redis_fallback` | 測試 Redis 降級 | LRU Cache 仍可用 | P1 |

---

### 5️⃣ Config Validation 測試 (V-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **V-001** | `test_config_structure_complete` | 驗證配置結構完整 | 所有必要鍵存在 | P0 |
| **V-002** | `test_quadrant_weights_sum_to_one` | 驗證權重總和 | 每個象限權重 = 1.0 | P0 |
| **V-003** | `test_thresholds_in_valid_range` | 驗證閾值範圍 | 0 ≤ threshold ≤ 1 | P0 |
| **V-004** | `test_candidate_counts_logic` | 驗證候選數邏輯 | top_k > filter_k > final | P0 |

---

### 6️⃣ Utilities 測試 (U-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **U-001** | `test_match_ratio_perfect_match` | 測試完美匹配 | ratio = 1.0 | P0 |
| **U-002** | `test_match_ratio_partial_match` | 測試部分匹配 | 0 < ratio < 1 | P0 |
| **U-003** | `test_match_ratio_no_match` | 測試無匹配 | ratio = 0.0 | P1 |
| **U-004** | `test_match_ratio_no_requirements` | 測試無要求 | ratio = 1.0 | P1 |
| **U-005** | `test_classify_q1_perfect` | 測試 Q1 分類 | quadrant = "q1_perfect_match" | P0 |
| **U-006** | `test_classify_q2_discovery` | 測試 Q2 分類 | quadrant = "q2_semantic_discovery" | P0 |
| **U-007** | `test_classify_q4_fallback` | 測試 Q4 分類 | quadrant = "q4_fallback" | P0 |
| **U-008** | `test_score_calculation_q1` | 測試 Q1 評分 | 使用平衡權重 | P1 |
| **U-009** | `test_year_range_check_valid` | 測試年份範圍（有效） | 返回 True | P1 |
| **U-010** | `test_year_range_check_invalid` | 測試年份範圍（無效） | 返回 False | P1 |

---

## 🔗 Level 2: 整合測試總表

### 📊 整合測試統計

| 模組 | 測試數量 | 測試 ID 範圍 | 檔案名稱 | 優先級 |
|------|---------|-------------|---------|--------|
| Recommendation Pipeline | 5 | I-001 ~ I-005 | `test_recommend_pipeline.py` | P0 |
| Cache Integration | 3 | CI-001 ~ CI-003 | `test_cache_integration.py` | P1 |
| Database Operations | 4 | DB-001 ~ DB-004 | `test_db_operations.py` | P1 |
| Quadrant Workflow | 3 | QW-001 ~ QW-003 | `test_quadrant_workflow.py` | P1 |
| **總計** | **15** | - | - | - |

---

### 整合測試詳細清單

#### Pipeline 測試 (I-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **I-001** | `test_full_pipeline_nl_only` | 測試完整流程（僅 NL） | 返回 10 部電影 | P0 |
| **I-002** | `test_full_pipeline_mood_only` | 測試完整流程（僅 Mood） | 返回推薦 + 象限分佈 | P0 |
| **I-003** | `test_full_pipeline_with_filters` | 測試帶過濾條件 | 正確應用過濾 | P0 |
| **I-004** | `test_pipeline_quadrant_distribution` | 測試象限分佈 | Q1 > Q2 > Q4 | P0 |
| **I-005** | `test_pipeline_with_cache` | 測試快取整合 | 第二次查詢命中快取 | P1 |

#### Cache Integration 測試 (CI-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **CI-001** | `test_embedding_cache_reduces_api_calls` | 驗證快取減少 API 呼叫 | 第二次不呼叫 API | P0 |
| **CI-002** | `test_recommendation_cache_improves_latency` | 驗證快取提升效能 | 快取命中 < 10ms | P1 |
| **CI-003** | `test_cache_invalidation_workflow` | 測試快取失效流程 | 失效後重新計算 | P1 |

#### Database Operations 測試 (DB-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **DB-001** | `test_vector_similarity_search` | 測試向量相似度搜索 | 返回 Top-K 結果 | P0 |
| **DB-002** | `test_multi_filter_combination` | 測試多重過濾組合 | 正確應用所有過濾 | P1 |
| **DB-003** | `test_year_range_filtering` | 測試年份範圍過濾 | 只返回範圍內電影 | P1 |
| **DB-004** | `test_genre_filtering` | 測試類型過濾 | 只返回指定類型 | P1 |

#### Quadrant Workflow 測試 (QW-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **QW-001** | `test_quadrant_classification_flow` | 測試象限分類流程 | 正確分配到三象限 | P0 |
| **QW-002** | `test_dynamic_scoring_flow` | 測試動態評分流程 | 各象限使用正確權重 | P0 |
| **QW-003** | `test_mixed_sorting_flow` | 測試混合排序流程 | 象限優先 + 分數次要 | P1 |

---

## 🎯 Level 3: 端到端測試總表

### 📊 E2E 測試統計

| 模組 | 測試數量 | 測試 ID 範圍 | 檔案名稱 | 優先級 |
|------|---------|-------------|---------|--------|
| Recommendation Scenarios | 4 | S-001 ~ S-004 | `test_recommendation_scenarios.py` | P1 |
| API Endpoints | 6 | API-001 ~ API-006 | `test_api_endpoints.py` | P1 |
| **總計** | **10** | - | - | - |

---

### E2E 測試詳細清單

#### Scenario 測試 (S-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **S-001** | `test_journey_scenario` | 測試 Journey 情境 | "難過的時候適合看什麼" + heartwarming | P0 |
| **S-002** | `test_paradox_scenario` | 測試 Paradox 情境 | "dark comedy" 推薦正確 | P1 |
| **S-003** | `test_multi_dimension_filtering` | 測試多維過濾 | Genres + Eras + Moods 同時應用 | P1 |
| **S-004** | `test_edge_case_few_candidates` | 測試邊界情況 | 極少候選時仍返回結果 | P1 |

#### API Endpoints 測試 (API-系列)

| ID | 測試名稱 | 測試目的 | 預期結果 | 優先級 |
|----|---------|---------|---------|--------|
| **API-001** | `test_recommend_endpoint_success` | 測試推薦端點成功 | 返回 200 + 電影列表 | P0 |
| **API-002** | `test_recommend_endpoint_validation` | 測試請求驗證 | 無效請求返回 400 | P1 |
| **API-003** | `test_cache_stats_endpoint` | 測試快取統計端點 | 返回正確統計 | P1 |
| **API-004** | `test_mood_labels_endpoint` | 測試 Mood 標籤端點 | 返回完整標籤列表 | P1 |
| **API-005** | `test_system_info_endpoint` | 測試系統資訊端點 | 返回版本與配置 | P2 |
| **API-006** | `test_cache_invalidation_endpoint` | 測試快取清除端點 | 成功清除快取 | P1 |

---

## 📅 實施時程表

### Week 1: 基礎建設
- [x] 創建測試目錄結構
- [ ] 設定 pytest 配置 (`pytest.ini`, `.coveragerc`)
- [ ] 實作共用 fixtures (`conftest.py`)
- [ ] 準備測試數據 (`fixtures/*.json`)

### Week 2: 核心單元測試 (P0)
- [ ] Embedding Service 測試 (E-001 ~ E-010) - **10 個**
- [ ] Query Generator 測試 (Q-001 ~ Q-009) - **9 個**
- [ ] Utilities 測試 (U-001 ~ U-010) - **10 個**
- **小計**: 29 個測試

### Week 3: 次要單元測試 (P1)
- [ ] Mood Analyzer 測試 (M-001 ~ M-009) - **9 個**
- [ ] Cache 測試 (C-001 ~ C-008) - **8 個**
- [ ] Config 測試 (V-001 ~ V-004) - **4 個**
- **小計**: 21 個測試

### Week 4: 整合測試
- [ ] Pipeline 測試 (I-001 ~ I-005) - **5 個**
- [ ] Cache Integration (CI-001 ~ CI-003) - **3 個**
- [ ] DB Operations (DB-001 ~ DB-004) - **4 個**
- [ ] Quadrant Workflow (QW-001 ~ QW-003) - **3 個**
- **小計**: 15 個測試

### Week 5: E2E 測試與優化
- [ ] Scenario 測試 (S-001 ~ S-004) - **4 個**
- [ ] API 測試 (API-001 ~ API-006) - **6 個**
- [ ] 生成覆蓋率報告
- [ ] 修復未達標模組
- **小計**: 10 個測試

---

## 🎯 優先級分配

### P0 (必須完成，Week 1-2)
- ✅ Embedding Service 核心功能
- ✅ Query Generator 三情境
- ✅ Utilities 核心函數
- ✅ Cache 命中/未命中
- ✅ Config 權重驗證
- ✅ Pipeline 完整流程
- **共計**: ~35 個測試

### P1 (重要，Week 3-4)
- ✅ Mood Analyzer 關係分析
- ✅ Cache TTL 與統計
- ✅ 整合測試大部分
- ✅ E2E Scenarios
- **共計**: ~30 個測試

### P2 (次要，Week 5)
- ✅ 邊界情況
- ✅ API 端點測試
- ✅ 性能測試
- **共計**: ~10 個測試

---

## 📊 測試覆蓋率追蹤表

| 模組 | 當前覆蓋率 | 目標覆蓋率 | 狀態 | 備註 |
|------|-----------|-----------|------|------|
| `simple_recommend.py` | 0% → ? | 85%+ | 🔴 未開始 | - |
| `embedding_service.py` | 0% → ? | 90%+ | 🔴 未開始 | - |
| `embedding_query_generator.py` | 0% → ? | 90%+ | 🔴 未開始 | - |
| `mood_analyzer.py` | 0% → ? | 85%+ | 🔴 未開始 | - |
| `recommendation_cache.py` | 0% → ? | 80%+ | 🔴 未開始 | - |
| `phase36_config.py` | 0% → ? | 100% | 🔴 未開始 | 配置檔 |
| **總計** | **0%** | **80%+** | 🔴 未開始 | - |

**圖例**:
- 🔴 未開始 (0-30%)
- 🟡 進行中 (30-70%)
- 🟢 已完成 (70%+)

---

## 🚀 快速執行指令

### 執行所有測試
```powershell
pytest -v
```

### 執行單元測試（快速）
```powershell
pytest tests/unit -v
```

### 執行特定模組測試
```powershell
# Embedding Service
pytest tests/unit/test_embedding_service.py -v

# Query Generator
pytest tests/unit/test_query_generator.py -v

# Mood Analyzer
pytest tests/unit/test_mood_analyzer.py -v
```

### 執行特定優先級
```powershell
# P0 測試
pytest -m "unit and not slow" -v

# 整合測試
pytest tests/integration -v
```

### 生成覆蓋率報告
```powershell
pytest --cov=app/services --cov-report=html --cov-report=term-missing
```

### 查看覆蓋率報告
```powershell
# 開啟 HTML 報告
start htmlcov/index.html
```

---

## 📈 進度追蹤檢查清單

### Phase 1: 基礎建設 ✅
- [ ] 創建 `backend/tests/` 目錄結構
- [ ] 創建 `pytest.ini`
- [ ] 創建 `.coveragerc`
- [ ] 創建 `conftest.py`
- [ ] 準備測試數據 fixtures
- [ ] 安裝測試依賴 (`pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-mock`)

### Phase 2: 單元測試 (50 個)
- [ ] E-001 ~ E-010: Embedding Service (10)
- [ ] Q-001 ~ Q-009: Query Generator (9)
- [ ] M-001 ~ M-009: Mood Analyzer (9)
- [ ] C-001 ~ C-008: Cache System (8)
- [ ] V-001 ~ V-004: Config Validation (4)
- [ ] U-001 ~ U-010: Utilities (10)

### Phase 3: 整合測試 (15 個)
- [ ] I-001 ~ I-005: Pipeline (5)
- [ ] CI-001 ~ CI-003: Cache Integration (3)
- [ ] DB-001 ~ DB-004: Database (4)
- [ ] QW-001 ~ QW-003: Quadrant Workflow (3)

### Phase 4: E2E 測試 (10 個)
- [ ] S-001 ~ S-004: Scenarios (4)
- [ ] API-001 ~ API-006: API Endpoints (6)

### Phase 5: 優化
- [ ] 達成 80%+ 覆蓋率
- [ ] 所有測試通過
- [ ] 性能基準建立
- [ ] CI/CD 整合

---

## 📝 測試執行紀錄範本

### 測試執行日誌

| 日期 | 執行範圍 | 通過/總數 | 覆蓋率 | 問題 | 備註 |
|------|---------|-----------|--------|------|------|
| 2025-12-11 | - | 0/0 | 0% | - | 初始化 |
| YYYY-MM-DD | Unit Tests | ?/50 | ?% | - | - |
| YYYY-MM-DD | Integration | ?/15 | ?% | - | - |
| YYYY-MM-DD | E2E Tests | ?/10 | ?% | - | - |
| YYYY-MM-DD | All Tests | ?/75 | ?% | - | 最終驗證 |

---

## 🎓 測試編寫檢查清單

每個測試都應該：
- [ ] 使用 AAA 模式 (Arrange-Act-Assert)
- [ ] 有清晰的測試名稱（描述測試目的）
- [ ] 包含文檔字串說明測試 ID 和目的
- [ ] Mock 外部依賴（API、Redis、Database）
- [ ] 獨立運行（不依賴其他測試）
- [ ] 斷言明確（使用 `pytest.approx` 處理浮點數）
- [ ] 快速執行（單元測試 < 100ms）

---

## 📚 相關文檔

- 📄 [完整測試架構文檔](./recommendation-system-unit-testing-architecture.md)
- 📄 [推薦系統架構文檔](./recommendation-system-architecture.md)
- 📄 [API 規格文檔](./api-specification.md)

---

**文檔結束**

*Generated by Winston - Holistic System Architect*  
*Date: 2025-12-11*
*Version: v1.0*
