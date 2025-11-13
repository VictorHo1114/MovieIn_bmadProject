# Phase 3.6: Embedding-First 架構決策文檔

## 決策資訊

**日期**：2025-11-13  
**架構師**：Winston  
**版本**：3.6  
**狀態**：✅ 設計完成，待實現

---

## 執行摘要

本文檔記錄了 MovieIn 推薦系統從 **Phase 3.5 (雙引擎並行)** 升級到 **Phase 3.6 (Embedding-First)** 的所有關鍵決策。

### 核心變革

```
舊架構 (Phase 3.5):
Feature Matching (主) → 生成 150 個候選
Embedding Reranking (輔) → 重排序這 150 個

新架構 (Phase 3.6):
Embedding Search (主) → 生成 300 個候選
Feature Filtering (輔) → 過濾這 300 個
```

### 戰略原因

**用戶洞察**："embedding 是準確的，我們可以更改策略...以 embedding 為主...用 feature based 做過濾"

**技術驗證**：
- Embedding 在模糊查詢上表現優異（語義理解強）
- Feature Matching 限制了 Embedding 的發現能力
- 反轉角色可以解放 Embedding 的潛力

---

## 五大核心決策

### 決策 1: Template 層次選擇

**問題**：情境 2（僅 Mood Labels）如何生成 Embedding Query？

**選項**：
- A. Simple Templates（簡單拼接）
- B. Relationship-aware Templates（關係感知）✅ **採用**
- C. Theme-aware Templates（主題感知）
- D. Mixed（混合使用）

**最終決策**：**B. Relationship-aware Templates**

**理由**：
1. Mood Labels 組合有明確的語義關係（journey、paradox、intensification）
2. 關係感知模板能精準表達這些關係
3. 比簡單模板準確，比主題模板易維護
4. 可擴展性強（通過 MOOD_RELATIONSHIP_MATRIX）

**實現**：
```python
MOOD_RELATIONSHIP_MATRIX = {
    ("sad", "healing"): {
        "type": "journey",
        "template": "A story about transformation from sadness to healing, emotional journey of recovery and hope"
    },
    ("dark", "lighthearted"): {
        "type": "paradox",
        "template": "A movie that blends dark themes with lighthearted moments, balancing humor and depth"
    },
    ("sad", "melancholy"): {
        "type": "intensification",
        "template": "A deeply emotional and melancholic story, profoundly sad and contemplative"
    }
}
```

---

### 決策 2: 衝突處理方法

**問題**：情境 3（NL + Mood Labels）且兩者矛盾時如何處理？

**範例衝突**：
```
Natural Language: "溫暖治癒的故事" (healing)
Mood Buttons: ["sad", "dark"]

→ 矛盾：NL 偏向正面，Mood 偏向負面
```

**選項**：
- A. Ignore Mood（忽略 Mood，僅用 NL）
- B. Deweight Mood（降低 Mood 權重）
- C. Separate Processing（分離處理）✅ **採用**

**最終決策**：**C. Separate Processing**

**理由**：
1. **自然語言優先原則**：用戶主動輸入的文字最能表達真實意圖
2. **Mood 仍有價值**：用於 Feature Filtering，不完全丟棄
3. **避免語義污染**：不將矛盾的 Mood 混入 Embedding Query
4. **兩階段驗證**：Embedding 找語義，Feature 驗證特徵

**實現流程**：
```python
if has_nl and has_moods:
    # 檢測衝突
    nl_sentiment = detect_sentiment(natural_query)  # "healing"
    mood_sentiment = detect_sentiment(mood_labels)  # "sad/dark"
    
    if nl_sentiment != mood_sentiment:
        # 分離處理
        embedding_query = natural_query  # NL 優先用於查詢
        filter_features = {
            "mood_tags": mood_labels,     # Mood 用於過濾
            "keywords": extracted_keywords
        }
    else:
        # 無衝突，合併使用
        embedding_query = merge_nl_and_moods(natural_query, mood_labels)
```

---

### 決策 3: Quadrant 設計

**問題**：Phase 3.5 的四象限系統需要重新設計嗎？

**Phase 3.5 四象限問題**：
```
舊架構：Match Ratio (Y 軸) × Embedding (X 軸)
→ 問題：Match Ratio 為主軸，不符合 Embedding-First 理念
→ Q2 (高 Match + 低 Emb) 權重過高，但在新架構中不重要
```

**選項**：
- A. 保留四象限，僅調整權重
- B. 三象限系統（合併 Q2 到 Q4）✅ **採用**
- C. 兩象限系統（高 Emb vs 低 Emb）

**最終決策**：**B. 三象限系統**

**理由**：
1. **軸心翻轉**：Embedding (Y 軸) × Match Ratio (X 軸) 更符合新架構
2. **Q2 不再重要**：高 Match + 低 Emb 在 Embedding-First 中很少出現
3. **簡化邏輯**：三象限更易理解和維護
4. **保留必要性**：Q1 (完美)、Q2 (語義)、Q4 (保底) 三者缺一不可

**新三象限定義**：

```
               Embedding Score (Y 軸 - 主)
                    ▲
                    │
        0.60 ───────┼───────────
           (高閾值) │
                    │
        Q1 完美匹配 │  Q2 語義發現
        E:50% F:30% │  E:70% F:10%
        M:20%       │  M:20%
    ────────────────┼────────────────► Match Ratio (X 軸 - 輔)
                    │           0.40
        Q4 保底     │          (低閾值)
        E:30% F:40% │
        M:30%       │
                    │
```

**閾值變更**：

| 閾值 | Phase 3.5 | Phase 3.6 | 變化 | 原因 |
|------|-----------|-----------|------|------|
| **high_embedding** | 0.45 | 0.60 | +0.15 | 提高標準，確保高品質 |
| **high_match** | 0.50 | 0.40 | -0.10 | 降低要求，Match 為輔助 |

**權重對照**：

| 象限 | E% | F% | M% | 說明 |
|------|----|----|----| -----|
| **Q1 完美匹配** | 50 | 30 | 20 | Embedding 主導，Feature 輔助 |
| **Q2 語義發現** | 70 | 10 | 20 | Embedding 極高，Feature 最低 |
| **Q4 保底** | 30 | 40 | 30 | 降權處理，Feature 提高 |

---

### 決策 4: 優先排序策略

**問題**：象限內的電影如何排序？

**選項**：
- A. Quadrant-first（象限優先，內部按 final_score）
- B. Score-first（全局按 final_score，忽略象限）
- C. Mixed（象限優先，內部按 Embedding）✅ **採用**

**最終決策**：**C. Mixed Strategy**

**理由**：
1. **象限優先原則**：確保 Q1 永遠在 Q2 前面
2. **Embedding 內部排序**：象限內按 Embedding Score 降序
3. **符合新架構**：Embedding-First → Embedding 為主要排序依據
4. **簡化計算**：不需要複雜的 final_score 加權

**實現**：
```python
def sort_by_quadrant_and_embedding(movies: List[Dict]) -> List[Dict]:
    """
    混合排序策略：
    1. 象限優先：Q1 > Q2 > Q4
    2. 象限內：Embedding Score 降序
    """
    quadrant_priority = {
        "q1_perfect_match": 1,
        "q2_semantic_discovery": 2,
        "q4_fallback": 3
    }
    
    return sorted(
        movies,
        key=lambda x: (
            quadrant_priority[x["quadrant"]],
            -x["embedding_score"]  # 降序
        )
    )
```

**排序範例**：
```
排序前（混亂）：
1. Q2, Emb=0.75
2. Q1, Emb=0.80
3. Q1, Emb=0.70
4. Q4, Emb=0.55
5. Q2, Emb=0.68

排序後（正確）：
1. Q1, Emb=0.80  ← Q1 優先，且 Emb 最高
2. Q1, Emb=0.70  ← Q1 優先，Emb 次高
3. Q2, Emb=0.75  ← Q2 次優先，Emb 最高
4. Q2, Emb=0.68  ← Q2 次優先，Emb 次高
5. Q4, Emb=0.55  ← Q4 最後
```

---

### 決策 5: Mood 分析方法

**問題**：如何分析 Mood Labels 組合的語義關係？

**選項**：
- A. Relationship Matrix（關係矩陣）
- B. Semantic Vector（語義向量）
- C. Hybrid（混合使用）✅ **採用**

**最終決策**：**C. Hybrid Approach**

**理由**：
1. **Matrix 優先**：覆蓋常見關係（journey、paradox、intensification）
2. **Vector 補充**：處理未知組合（使用 Embedding 計算語義距離）
3. **可擴展性**：Matrix 易維護，Vector 自動學習
4. **效能平衡**：Matrix 快速查詢，Vector 按需計算

**實現架構**：

```python
def analyze_mood_combination(mood_labels: List[str]) -> Dict:
    """
    混合方法：Matrix 優先，Vector 補充
    """
    # Phase 1: 檢查已知關係（Matrix）
    for (mood1, mood2), relationship in MOOD_RELATIONSHIP_MATRIX.items():
        if mood1 in mood_labels and mood2 in mood_labels:
            return {
                "type": relationship["type"],
                "template": relationship["template"],
                "confidence": "high",
                "source": "matrix"
            }
    
    # Phase 2: 語義向量分析（Vector）
    if len(mood_labels) >= 2:
        # 計算 Mood Labels 的語義相似度
        embeddings = [get_mood_embedding(mood) for mood in mood_labels]
        avg_similarity = calculate_pairwise_similarity(embeddings)
        
        if avg_similarity > 0.7:
            return {
                "type": "intensification",
                "template": "complex_similar",
                "confidence": "medium",
                "source": "vector"
            }
        elif avg_similarity < 0.3:
            return {
                "type": "paradox",
                "template": "complex_contrast",
                "confidence": "medium",
                "source": "vector"
            }
        else:
            return {
                "type": "multi-faceted",
                "template": "complex_mixed",
                "confidence": "low",
                "source": "vector"
            }
    
    # Fallback: 單一 Mood 或無法判斷
    return {
        "type": "simple",
        "template": "simple",
        "confidence": "high",
        "source": "default"
    }
```

**MOOD_RELATIONSHIP_MATRIX 範例**：

```python
MOOD_RELATIONSHIP_MATRIX = {
    # Journey (轉變)
    ("sad", "healing"): {
        "type": "journey",
        "description": "Emotional transformation from sadness to healing",
        "template": "A story about overcoming sadness and finding healing, emotional journey of recovery and hope"
    },
    ("dark", "uplifting"): {
        "type": "journey",
        "description": "Journey from darkness to light",
        "template": "A narrative that moves from dark themes towards uplifting moments, finding light in darkness"
    },
    
    # Paradox (矛盾)
    ("dark", "lighthearted"): {
        "type": "paradox",
        "description": "Contrasting blend of dark and light",
        "template": "A movie that blends dark themes with lighthearted moments, balancing humor and depth"
    },
    ("sad", "fun"): {
        "type": "paradox",
        "description": "Bittersweet combination",
        "template": "A bittersweet story mixing sadness with fun moments, emotional complexity"
    },
    
    # Intensification (強化)
    ("sad", "melancholy"): {
        "type": "intensification",
        "description": "Deep sadness reinforcement",
        "template": "A deeply emotional and melancholic story, profoundly sad and contemplative"
    },
    ("dark", "gritty"): {
        "type": "intensification",
        "description": "Dark atmosphere intensification",
        "template": "An intensely dark and gritty film, raw and unflinching"
    },
    
    # ... 50+ more relationships
}
```

**Vector Fallback 範例**：

```python
# 未知組合：["nostalgic", "adventurous"]
# Matrix 中沒有這個組合

# Vector 分析：
embeddings = [
    get_mood_embedding("nostalgic"),  # [0.2, 0.8, 0.3, ...]
    get_mood_embedding("adventurous")  # [0.7, 0.2, 0.6, ...]
]
similarity = cosine_similarity(embeddings[0], embeddings[1])  # 0.45

# 結果：中等相似度 → "multi-faceted"
# 模板：「A nostalgic yet adventurous story」
```

---

## 決策矩陣總覽

| 決策點 | 選項 A | 選項 B | 選項 C | 選項 D | 最終決策 |
|--------|--------|--------|--------|--------|----------|
| **1. Template 層次** | Simple | **Relationship-aware** ✅ | Theme-aware | Mixed | B |
| **2. 衝突處理** | Ignore | Deweight | **Separate** ✅ | - | C |
| **3. Quadrant 設計** | 4 象限調整 | **3 象限** ✅ | 2 象限 | - | B |
| **4. 排序策略** | Quadrant-first | Score-first | **Mixed** ✅ | - | C |
| **5. Mood 分析** | Matrix | Vector | **Hybrid** ✅ | - | C |

---

## 配置變更總結

### Phase 3.5 → Phase 3.6 對照

```python
# Phase 3.5 Config
PHASE35_CONFIG = {
    "architecture": "dual_engine_parallel",
    "primary_engine": "feature_matching",
    "secondary_engine": "embedding_reranking",
    "quadrants": 4,
    "quadrant_axes": "Match (Y) × Embedding (X)",
    "thresholds": {
        "high_match": 0.50,
        "high_embedding": 0.45
    },
    "candidate_counts": {
        "feature_candidates": 150,
        "final": 10
    }
}

# Phase 3.6 Config
PHASE36_CONFIG = {
    "architecture": "embedding_first",
    "primary_engine": "embedding_search",
    "secondary_engine": "feature_filtering",
    "quadrants": 3,
    "quadrant_axes": "Embedding (Y) × Match (X)",
    "thresholds": {
        "high_embedding": 0.60,  # ↑ +0.15
        "high_match": 0.40       # ↓ -0.10
    },
    "candidate_counts": {
        "embedding_candidates": 300,  # NEW
        "filtered_candidates": 150,   # NEW
        "final": 10
    },
    "mood_analysis": {
        "method": "hybrid",
        "matrix_priority": True,
        "vector_fallback": True
    },
    "conflict_handling": "separate"
}
```

---

## 預期影響

### 性能指標

| 指標 | Phase 3.5 | Phase 3.6 | 變化 |
|------|-----------|-----------|------|
| **候選覆蓋** | 150 部 | 300 部 | +100% |
| **語義準確度** | 70% | 85% | +15% |
| **模糊查詢** | 中等 | 優秀 | ⬆️ |
| **精確查詢** | 優秀 | 良好 | ⬇️ (可接受) |
| **Mood 組合** | 不支援 | 支援 | ✅ |
| **查詢延遲** | ~120ms | ~180ms | +50% |
| **API 成本** | $0.00002 | $0.00002 | 無變化 |

### 用戶體驗

**優勢**：
- ✅ 模糊查詢更準確（"下雨天的電影"、"失戀時看的"）
- ✅ Mood 組合語義理解（"sad + healing" → journey）
- ✅ 發現更多語義相關電影（不受 Feature 限制）
- ✅ 自然語言優先（符合用戶直覺）

**權衡**：
- ⚠️ 精確選擇可能略降（Feature 僅為過濾）
- ⚠️ 計算延遲增加 50%（可接受範圍）
- ⚠️ 複雜度提高（需更多測試）

### 技術債務

**新增技術債**：
- 需維護 MOOD_RELATIONSHIP_MATRIX（50+ 關係）
- Embedding 全庫搜索性能監控（667 部 → 未來擴展）
- 三象限權重需持續調優

**解決技術債**：
- ✅ Feature 限制問題（Phase 3.5 的最大問題）
- ✅ 雙引擎耦合問題（清晰分工）
- ✅ Mood 組合理解缺失（新增支援）

---

## 實現檢查清單

### 核心函數開發

- [ ] **generate_embedding_query()**
  - [ ] 情境 1: 僅 NL
  - [ ] 情境 2: 僅 Mood（關係感知模板）
  - [ ] 情境 3: NL + Mood（分離處理）
  - [ ] 衝突檢測邏輯

- [ ] **analyze_mood_combination()**
  - [ ] MOOD_RELATIONSHIP_MATRIX 建立（50+ 關係）
  - [ ] Matrix 查詢邏輯
  - [ ] Vector 補充邏輯（語義距離計算）
  - [ ] Fallback 機制

- [ ] **embedding_similarity_search()**
  - [ ] 全庫 Embedding 查詢
  - [ ] Cosine Similarity 計算
  - [ ] Top 300 排序
  - [ ] 性能優化（批次處理）

- [ ] **tiered_feature_filtering()** (重構)
  - [ ] 接受 Embedding 候選作為輸入
  - [ ] 三層過濾邏輯
  - [ ] Match Ratio 計算
  - [ ] Feature Score 計算

- [ ] **classify_to_3quadrant()**
  - [ ] 三象限分類邏輯
  - [ ] 新閾值應用（0.60 / 0.40）
  - [ ] 象限標籤返回

- [ ] **calculate_3quadrant_score()**
  - [ ] 三象限權重應用
  - [ ] Final Score 計算

- [ ] **sort_by_quadrant_and_embedding()**
  - [ ] 象限優先排序
  - [ ] 象限內 Embedding 排序

### 數據建立

- [ ] **MOOD_RELATIONSHIP_MATRIX**
  - [ ] Journey 關係（10+ 對）
  - [ ] Paradox 關係（10+ 對）
  - [ ] Intensification 關係（10+ 對）
  - [ ] Multi-faceted 關係（20+ 對）

- [ ] **Template 庫**
  - [ ] Journey templates
  - [ ] Paradox templates
  - [ ] Intensification templates
  - [ ] Fallback templates

### 測試開發

- [ ] **test_phase36_embedding_first.py**
  - [ ] 情境 1 測試
  - [ ] 情境 2 測試
  - [ ] 情境 3 測試（衝突）
  - [ ] 三象限分類測試
  - [ ] Mood 關係分析測試
  - [ ] 端到端推薦測試

- [ ] **test_mood_relationships.py**
  - [ ] Matrix 查詢測試
  - [ ] Vector fallback 測試
  - [ ] Template 生成測試

- [ ] **test_3quadrant_logic.py**
  - [ ] 分類邏輯測試
  - [ ] 權重計算測試
  - [ ] 排序邏輯測試

### 文檔更新

- [x] **recommendation-system-architecture.md**
  - [x] 新增 Phase 3.6 章節
  - [x] 更新系統架構圖
  - [x] 更新配置說明

- [ ] **API 文檔**
  - [ ] 新增 quadrant 欄位說明
  - [ ] 新增 mood_relationship 欄位

- [ ] **前端文檔**
  - [ ] 三象限 UI 設計
  - [ ] Mood 關係顯示

### 性能測試

- [ ] **A/B 測試框架**
  - [ ] Phase 3.5 vs 3.6 對照組
  - [ ] 用戶滿意度追蹤
  - [ ] 點擊率監控

- [ ] **壓力測試**
  - [ ] 300 候選性能測試
  - [ ] 全庫 Embedding 搜索延遲
  - [ ] 並發請求測試

---

## 風險與緩解

### 技術風險

| 風險 | 嚴重性 | 緩解措施 |
|------|--------|----------|
| **全庫搜索延遲** | 中 | 1. 批次優化<br>2. 未來使用 pgvector<br>3. 監控並設定超時 |
| **Matrix 維護成本** | 低 | 1. 分階段建立（先 20 對）<br>2. 社群貢獻<br>3. Vector 自動補充 |
| **閾值不準確** | 中 | 1. A/B 測試驗證<br>2. 可配置化<br>3. 持續調優 |
| **精確查詢降級** | 低 | 1. Q1 權重保護<br>2. 監控指標<br>3. 回退機制 |

### 產品風險

| 風險 | 嚴重性 | 緩解措施 |
|------|--------|----------|
| **用戶不理解變化** | 低 | 1. 前端透明化<br>2. "為什麼推薦" 解釋<br>3. 逐步推出 |
| **推薦品質下降** | 中 | 1. A/B 測試先行<br>2. 設定品質閾值<br>3. 快速回退機制 |
| **複雜度過高** | 低 | 1. 充分測試<br>2. 文檔完善<br>3. Debug 模式 |

---

## 未來擴展

### Phase 3.7: Vector Database (考慮中)

當電影數量增長到 10,000+ 時：
```
選項 1: PostgreSQL pgvector 擴展
選項 2: Pinecone / Weaviate (專用向量資料庫)
選項 3: FAISS (Facebook AI Similarity Search)

推薦：先用 pgvector，達 100,000+ 再考慮專用 DB
```

### Phase 3.8: 動態 Matrix 學習

```python
# 自動學習新的 Mood 關係
def learn_mood_relationship_from_user_feedback():
    """
    基於用戶行為學習新的 Mood 組合關係
    
    例如：用戶經常點擊 ["nostalgic", "adventurous"] 的電影
    → 自動識別為 "multi-faceted" 關係
    → 生成並加入 Matrix
    """
    pass
```

### Phase 3.9: 多模態 Embedding

```python
# 結合多種 Embedding
embeddings = {
    "text": text_embedding_3_small(movie_text),
    "image": clip_embedding(poster_image),
    "audio": wav2vec_embedding(trailer_audio)
}

# 融合多模態特徵
final_embedding = fuse_multimodal(embeddings)
```

---

## 決策批准

**技術批准**：Winston (Architect) ✅  
**產品批准**：待定  
**實現時間**：預計 2 週  
**測試時間**：預計 1 週  
**上線計劃**：A/B 測試 → 灰度發布 → 全量上線

---

**文檔版本**：1.0  
**最後更新**：2025-11-13  
**作者**：Winston  
**狀態**：✅ 決策完成，待實現