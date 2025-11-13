"""
Phase 3.6 配置文件
Embedding-First 推薦系統的所有閾值和權重配置

這個文件集中管理所有可調參數，方便調優而無需修改代碼。
"""

# ============================================================================
# Phase 3.6 核心配置
# ============================================================================

PHASE36_CONFIG = {
    # ========================================================================
    # 象限分類閾值
    # ========================================================================
    "quadrant_thresholds": {
        # Embedding 相似度閾值（0-1）
        # Phase 3.6: 提高到 0.60（Phase 3.5 為 0.45）
        # 更高的閾值意味著更嚴格的語義相似度要求
        "high_embedding": 0.60,
        
        # Match Ratio 閾值（0-1）
        # Phase 3.6: 降低到 0.40（Phase 3.5 為 0.50）
        # 更低的閾值使得 Feature Matching 門檻放寬
        "high_match": 0.40,
    },
    
    # ========================================================================
    # 象限權重配置（動態權重）
    # ========================================================================
    "quadrant_weights": {
        # Q1 (Perfect Match): High Embedding + High Match
        # 平衡策略：Embedding 略高，Feature 和 Match 輔助
        "q1_perfect_match": {
            "embedding": 0.50,      # 50% - Embedding 為主
            "feature": 0.30,        # 30% - Feature 輔助（預留但暫不使用）
            "match_ratio": 0.20,    # 20% - Match Ratio 輔助
        },
        
        # Q2 (Semantic Discovery): High Embedding + Low Match
        # Embedding 優先策略：發現語義相關但特徵不完全匹配的電影
        "q2_semantic_discovery": {
            "embedding": 0.70,      # 70% - Embedding 為主導
            "feature": 0.10,        # 10% - Feature 最小化
            "match_ratio": 0.20,    # 20% - Match Ratio 保留
        },
        
        # Q4 (Fallback): Low Embedding
        # Feature 優先策略：當語義相似度不足時依賴特徵匹配
        "q4_fallback": {
            "embedding": 0.30,      # 30% - Embedding 降低
            "feature": 0.40,        # 40% - Feature 為主（預留）
            "match_ratio": 0.30,    # 30% - Match Ratio 提升
        },
    },
    
    # ========================================================================
    # 候選數量配置
    # ========================================================================
    "candidate_counts": {
        # Step 1: Embedding 搜索返回的候選數
        "embedding_top_k": 300,
        
        # Step 2: Feature Filtering 後的候選數
        "feature_filter_k": 150,
        
        # Step 3: 最終返回的推薦數
        "final_recommendations": 10,
        
        # Step 7: 智能選取策略
        "guaranteed_top": 3,      # 固定返回的 Top N（保證質量）
        "random_pool_size": 30,   # 隨機選取的候選池大小（排名 4-30）
    },
    
    # ========================================================================
    # Embedding 搜索配置
    # ========================================================================
    "embedding_search": {
        # 最低相似度閾值（過濾掉相似度過低的電影）
        "min_similarity": 0.0,  # 0.0 表示不過濾
        
        # 是否啟用多樣性機制（Phase 3.6 暫不使用，保留給未來）
        "enable_diversity": False,
        "diversity_weight": 0.3,
    },
    
    # ========================================================================
    # Feature Filtering 配置
    # ========================================================================
    "feature_filtering": {
        # Tier 閾值
        "tier1_threshold": 0.80,  # >= 80% 符合
        "tier2_threshold": 0.50,  # >= 50% 符合
        # Tier 3: < 50% 符合（保底）
        
        # 隨機性參數（0.0 完全確定，1.0 完全隨機）
        "randomness": 0.3,
    },
    
    # ========================================================================
    # Query Generation 配置
    # ========================================================================
    "query_generation": {
        # 是否啟用衝突檢測
        "enable_conflict_detection": True,
        
        # 空查詢的預設文本
        "fallback_query": "popular and highly rated movies",
    },
    
    # ========================================================================
    # 調試與日誌
    # ========================================================================
    "debug": {
        # 是否打印詳細日誌
        "verbose": True,
        
        # 是否打印每個階段的候選數
        "print_candidate_counts": True,
        
        # 是否打印象限分佈統計
        "print_quadrant_stats": True,
    },
}


# ============================================================================
# 輔助函數
# ============================================================================

def get_config(key_path: str = None):
    """
    獲取配置值
    
    Args:
        key_path: 配置路徑，使用點號分隔，例如 "quadrant_thresholds.high_embedding"
                 如果為 None，返回完整配置
    
    Returns:
        配置值
    
    Example:
        >>> get_config("quadrant_thresholds.high_embedding")
        0.60
        >>> get_config("candidate_counts")
        {"embedding_top_k": 300, "feature_filter_k": 150, ...}
    """
    if key_path is None:
        return PHASE36_CONFIG
    
    keys = key_path.split(".")
    value = PHASE36_CONFIG
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    
    return value


def update_config(key_path: str, new_value):
    """
    更新配置值（運行時動態調整）
    
    Args:
        key_path: 配置路徑
        new_value: 新值
    
    Example:
        >>> update_config("quadrant_thresholds.high_embedding", 0.65)
        >>> get_config("quadrant_thresholds.high_embedding")
        0.65
    """
    keys = key_path.split(".")
    current = PHASE36_CONFIG
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = new_value


def print_config():
    """打印完整配置（用於調試）"""
    import json
    print("\n" + "="*70)
    print("Phase 3.6 Configuration")
    print("="*70)
    print(json.dumps(PHASE36_CONFIG, indent=2, ensure_ascii=False))
    print("="*70 + "\n")


# ============================================================================
# 配置驗證
# ============================================================================

def validate_config():
    """
    驗證配置的合理性
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # 驗證閾值範圍
    high_embedding = PHASE36_CONFIG["quadrant_thresholds"]["high_embedding"]
    high_match = PHASE36_CONFIG["quadrant_thresholds"]["high_match"]
    
    if not (0 <= high_embedding <= 1):
        errors.append(f"high_embedding must be in [0, 1], got {high_embedding}")
    
    if not (0 <= high_match <= 1):
        errors.append(f"high_match must be in [0, 1], got {high_match}")
    
    # 驗證權重總和（應該接近 1.0）
    for quadrant, weights in PHASE36_CONFIG["quadrant_weights"].items():
        total = sum(weights.values())
        if not (0.95 <= total <= 1.05):  # 允許 5% 誤差
            errors.append(f"{quadrant} weights sum to {total:.2f}, should be ~1.0")
    
    # 驗證候選數量遞減
    counts = PHASE36_CONFIG["candidate_counts"]
    if not (counts["embedding_top_k"] >= counts["feature_filter_k"] >= counts["final_recommendations"]):
        errors.append("Candidate counts must be decreasing: embedding_top_k >= feature_filter_k >= final_recommendations")
    
    return len(errors) == 0, errors


if __name__ == "__main__":
    # 測試配置
    print_config()
    
    # 驗證配置
    is_valid, errors = validate_config()
    if is_valid:
        print("[PASS] Configuration is valid!")
    else:
        print("[FAIL] Configuration has errors:")
        for error in errors:
            print(f"  - {error}")
