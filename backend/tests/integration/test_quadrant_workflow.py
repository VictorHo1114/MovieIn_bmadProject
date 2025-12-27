"""
Integration Tests for Quadrant Workflow
測試 Quadrant 工作流程整合
"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key-for-testing-only"
os.environ["TESTING"] = "1"

import pytest
from typing import List, Dict
from unittest.mock import Mock, patch

from app.services.embedding_query_generator import generate_embedding_query
from app.services.mood_analyzer import analyze_mood_combination


class TestQuadrantWorkflow:
    """測試 Quadrant 推薦工作流"""
    
    @pytest.mark.integration
    def test_i015_quadrant_mood_to_query(self):
        """I-015: Quadrant → Mood Labels → Embedding Query"""
        # Arrange - 模擬 Quadrant 1 (Uplifting & Light)
        quadrant_moods = ["uplifting", "cheerful", "lighthearted"]
        
        # Act - Step 1: Analyze mood combination
        mood_analysis = analyze_mood_combination(quadrant_moods)
        
        # Act - Step 2: Generate embedding query
        query_result = generate_embedding_query("", quadrant_moods, mood_analysis)
        
        # Assert
        assert query_result["scenario"] in ["mood_only", "simple"]
        assert len(query_result["query"]) > 0
        assert "uplifting" in query_result["query"].lower() or "cheerful" in query_result["query"].lower()
