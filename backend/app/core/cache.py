"""
Redis 快取服務
提供統一的快取介面，用於訊息系統效能優化
"""
import os
import json
import logging
from typing import Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Redis 客戶端（延遲載入）
_redis_client = None

def get_redis_client():
    """取得 Redis 客戶端（單例模式）"""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        import redis
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        
        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        
        # 測試連線
        _redis_client.ping()
        logger.info(f"Redis connected: {redis_host}:{redis_port}/{redis_db}")
        
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
        _redis_client = None
    
    return _redis_client


class CacheService:
    """快取服務類"""
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """取得快取值"""
        client = get_redis_client()
        if not client:
            return None
        
        try:
            value = client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
        
        return None
    
    @staticmethod
    def set(key: str, value: Any, ttl: int = 60):
        """設定快取值
        
        Args:
            key: 快取鍵
            value: 快取值（會自動 JSON 序列化）
            ttl: 過期時間（秒），預設 60 秒
        """
        client = get_redis_client()
        if not client:
            return False
        
        try:
            serialized = json.dumps(value)
            client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    @staticmethod
    def delete(key: str):
        """刪除快取"""
        client = get_redis_client()
        if not client:
            return False
        
        try:
            client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    @staticmethod
    def invalidate_pattern(pattern: str):
        """刪除符合模式的所有快取
        
        Args:
            pattern: 鍵模式，例如 "user:123:*"
        """
        client = get_redis_client()
        if not client:
            return 0
        
        try:
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate error for pattern '{pattern}': {e}")
            return 0


def cache_result(key_prefix: str, ttl: int = 60):
    """裝飾器：快取函數結果
    
    Args:
        key_prefix: 快取鍵前綴
        ttl: 過期時間（秒）
    
    Usage:
        @cache_result("unread_count", ttl=60)
        def get_unread_count(user_id: str):
            # ... 查詢邏輯
            return count
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成快取鍵（簡化版，可根據需求改進）
            cache_key = f"{key_prefix}:{':'.join(map(str, args))}"
            
            # 嘗試從快取取得
            cached = CacheService.get(cache_key)
            if cached is not None:
                logger.debug(f"[Cache HIT] {cache_key}")
                return cached
            
            # 快取未命中，執行函數
            logger.debug(f"[Cache MISS] {cache_key}")
            result = func(*args, **kwargs)
            
            # 寫入快取
            CacheService.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# 訊息系統專用快取鍵生成器
class MessageCacheKeys:
    """訊息系統快取鍵管理"""
    
    @staticmethod
    def unread_count(user_id: str) -> str:
        return f"msg:unread:{user_id}"
    
    @staticmethod
    def conversations(user_id: str) -> str:
        return f"msg:conversations:{user_id}"
    
    @staticmethod
    def user_online(user_id: str) -> str:
        return f"msg:online:{user_id}"
    
    @staticmethod
    def invalidate_user_messages(user_id: str):
        """清除用戶所有訊息相關快取"""
        CacheService.invalidate_pattern(f"msg:*:{user_id}")
