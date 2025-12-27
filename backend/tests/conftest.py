# tests/conftest.py
"""
Pytest 配置與共用 Fixtures
Pytest Configuration and Shared Fixtures

提供測試所需的共用資源：
- 資料庫連線
- 測試數據
- Mock 物件
- 環境配置
"""
import os
import sys
import pytest
import asyncio
from typing import Generator, Dict, List, Any
from datetime import datetime
from unittest.mock import Mock, patch

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


# ============================================================================
# pytest 配置
# ============================================================================

def pytest_configure(config):
    """Pytest 配置"""
    config.addinivalue_line(
        "markers", "unit: 單元測試標記"
    )
    config.addinivalue_line(
        "markers", "integration: 整合測試標記"
    )
    config.addinivalue_line(
        "markers", "e2e: 端到端測試標記"
    )


# ============================================================================
# 環境配置 Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_env():
    """測試環境配置"""
    return {
        "OPENAI_API_KEY": "sk-test-fake-key-for-testing-only",
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/1",
        "ENV": "test",
        "TESTING": "1"
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_env(test_env):
    """設置測試環境變數（在所有測試之前自動執行）"""
    # 在導入任何 app 模組之前設置環境變數
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Cleanup - 恢復原始環境變數
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


# ============================================================================
# 資料庫 Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def db_engine(test_env):
    """
    創建測試資料庫引擎
    使用 StaticPool 以支持 SQLite 內存資料庫
    """
    # 使用 SQLite 內存資料庫進行測試（快速）
    # 如需完整測試，使用 PostgreSQL: test_env["DATABASE_URL"]
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # 創建表（需要導入 models）
    # from db.database import Base
    # Base.metadata.create_all(engine)
    
    yield engine
    
    # 清理
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    創建測試資料庫 Session
    每個測試函數都會獲得一個新的 session
    測試結束後自動 rollback
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    
    yield session
    
    # 清理：rollback 所有更改
    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI Client"""
    with patch('app.services.embedding_service.client') as mock_client:
        # Mock embeddings.create 方法
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create.return_value = mock_response
        yield mock_client


@pytest.fixture
def mock_redis_client():
    """Mock Redis Client"""
    with patch('app.services.recommendation_cache.redis_client') as mock_redis:
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        yield mock_redis


# ============================================================================
# 測試數據 Fixtures
# ============================================================================

@pytest.fixture
def sample_movies() -> List[Dict[str, Any]]:
    """
    樣本電影數據
    模擬資料庫中的電影記錄
    """
    return [
        {
            "id": 550,
            "tmdb_id": 550,
            "title": "It's a Wonderful Life",
            "overview": "A heartwarming story about a man who discovers the value of life.",
            "genres": ["剧情"],
            "mood_tags": ["heartwarming", "uplifting", "emotional"],
            "keywords": ["family", "hope", "redemption"],
            "vote_average": 8.5,
            "vote_count": 5000,
            "release_date": "1946-12-20",
            "poster_path": "/poster1.jpg",
            "embedding": [0.5] * 1536  # Mock embedding
        },
        {
            "id": 551,
            "tmdb_id": 551,
            "title": "The Dark Knight",
            "overview": "A dark and gritty superhero film.",
            "genres": ["动作", "犯罪", "剧情"],
            "mood_tags": ["dark", "gritty", "intense"],
            "keywords": ["superhero", "crime", "justice"],
            "vote_average": 9.0,
            "vote_count": 25000,
            "release_date": "2008-07-18",
            "poster_path": "/poster2.jpg",
            "embedding": [0.3] * 1536
        },
        {
            "id": 552,
            "tmdb_id": 552,
            "title": "Amélie",
            "overview": "A whimsical romantic comedy.",
            "genres": ["喜剧", "爱情"],
            "mood_tags": ["whimsical", "lighthearted", "romantic"],
            "keywords": ["paris", "love", "imagination"],
            "vote_average": 8.3,
            "vote_count": 7000,
            "release_date": "2001-04-25",
            "poster_path": "/poster3.jpg",
            "embedding": [0.7] * 1536
        }
    ]


@pytest.fixture
def sample_embeddings() -> Dict[str, List[float]]:
    """
    樣本 Embedding 向量
    用於測試相似度計算
    """
    return {
        "heartwarming story": [0.5] * 1536,
        "dark thriller": [0.3] * 1536,
        "romantic comedy": [0.7] * 1536,
        "action adventure": [0.4] * 1536,
    }


@pytest.fixture
def sample_queries() -> List[Dict[str, Any]]:
    """
    樣本查詢數據
    用於測試推薦流程
    """
    return [
        {
            "natural_query": "難過的時候適合看什麼電影",
            "mood_labels": ["heartwarming", "uplifting"],
            "genres": ["Drama"],
            "expected_scenario": "both"
        },
        {
            "natural_query": None,
            "mood_labels": ["emotional", "heartwarming"],
            "genres": [],
            "expected_scenario": "mood_only"
        },
        {
            "natural_query": "I want a funny movie",
            "mood_labels": [],
            "genres": ["Comedy"],
            "expected_scenario": "nl_only"
        }
    ]


@pytest.fixture
def sample_mood_relationships() -> Dict:
    """
    樣本 Mood 關係數據
    用於測試 Mood Analyzer
    """
    return {
        "journey": {
            "moods": ["emotional", "heartwarming"],
            "type": "journey",
            "template": "A heartwarming story about emotional healing"
        },
        "paradox": {
            "moods": ["dark", "lighthearted"],
            "type": "paradox",
            "template": "A dark comedy blending serious themes with humor"
        }
    }


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def clear_cache():
    """
    清除快取
    在需要測試快取邏輯時使用
    """
    from app.services.recommendation_cache import invalidate_recommendation_cache
    
    # Setup: 清除快取
    invalidate_recommendation_cache()
    
    yield
    
    # Teardown: 再次清除
    invalidate_recommendation_cache()


@pytest.fixture
def freeze_time():
    """
    凍結時間（用於測試 TTL 等時間相關功能）
    需要安裝 freezegun: pip install freezegun
    """
    try:
        from freezegun import freeze_time
        return freeze_time
    except ImportError:
        pytest.skip("freezegun not installed")


# ============================================================================
# Async Fixtures (for asyncio tests)
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    創建 event loop
    用於 asyncio 測試
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# 輔助函數
# ============================================================================

@pytest.fixture
def assert_approx():
    """
    浮點數近似比較輔助函數
    """
    def _assert_approx(actual: float, expected: float, abs_tol: float = 1e-6):
        assert abs(actual - expected) < abs_tol, \
            f"Expected {expected}, got {actual} (tolerance: {abs_tol})"
    return _assert_approx


@pytest.fixture
def create_mock_movie():
    """
    創建 Mock 電影數據的工廠函數
    """
    def _create(
        title: str = "Test Movie",
        genres: List[str] = None,
        mood_tags: List[str] = None,
        keywords: List[str] = None,
        match_ratio: float = 0.5,
        embedding_score: float = 0.6
    ) -> Dict[str, Any]:
        return {
            "id": 999,
            "title": title,
            "genres": genres or ["剧情"],
            "mood_tags": mood_tags or ["emotional"],
            "keywords": keywords or ["test"],
            "match_ratio": match_ratio,
            "embedding_score": embedding_score,
            "vote_average": 7.5,
            "overview": f"Overview of {title}",
            "release_date": "2020-01-01"
        }
    return _create


# ============================================================================
# 測試標記輔助
# ============================================================================

@pytest.fixture(autouse=True)
def skip_if_no_db(request, db_session):
    """
    如果測試需要資料庫但資料庫不可用，則跳過
    """
    if request.node.get_closest_marker('db'):
        if db_session is None:
            pytest.skip("Database not available")


@pytest.fixture(autouse=True)
def skip_if_slow(request):
    """
    如果執行快速測試模式，跳過耗時測試
    """
    if request.config.getoption("--fast", default=False):
        if request.node.get_closest_marker('slow'):
            pytest.skip("Skipping slow test in fast mode")


# ============================================================================
# Pytest 命令行選項
# ============================================================================

def pytest_addoption(parser):
    """添加自定義命令行選項"""
    parser.addoption(
        "--fast",
        action="store_true",
        default=False,
        help="Run only fast tests (skip slow tests)"
    )
    parser.addoption(
        "--use-real-db",
        action="store_true",
        default=False,
        help="Use real database instead of SQLite in-memory"
    )
