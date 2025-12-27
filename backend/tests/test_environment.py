"""
測試環境驗證
Test Environment Validation

此測試文件用於驗證測試環境設置正確
"""
import pytest


class TestEnvironment:
    """測試環境驗證"""
    
    def test_pytest_working(self):
        """驗證 pytest 正常運作"""
        assert True
    
    def test_basic_math(self):
        """驗證基本斷言"""
        assert 1 + 1 == 2
        assert "hello" == "hello"
    
    def test_list_operations(self):
        """驗證列表操作"""
        test_list = [1, 2, 3]
        assert len(test_list) == 3
        assert 2 in test_list
    
    def test_approx_floats(self):
        """驗證浮點數近似比較"""
        assert pytest.approx(0.1 + 0.2, abs=1e-6) == 0.3


class TestFixtures:
    """測試 Fixtures 是否正常載入"""
    
    def test_sample_movies_fixture(self, sample_movies):
        """驗證 sample_movies fixture"""
        assert isinstance(sample_movies, list)
        assert len(sample_movies) > 0
        assert "title" in sample_movies[0]
    
    def test_sample_embeddings_fixture(self, sample_embeddings):
        """驗證 sample_embeddings fixture"""
        assert isinstance(sample_embeddings, dict)
        assert "heartwarming story" in sample_embeddings
    
    def test_create_mock_movie_fixture(self, create_mock_movie):
        """驗證 create_mock_movie fixture"""
        movie = create_mock_movie(title="Test Movie")
        assert movie["title"] == "Test Movie"
        assert "match_ratio" in movie


@pytest.mark.asyncio
async def test_async_support():
    """驗證 asyncio 支持"""
    async def async_function():
        return "async works"
    
    result = await async_function()
    assert result == "async works"


def test_markers():
    """驗證測試標記"""
    # 此測試本身就是驗證標記系統能正常工作
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
