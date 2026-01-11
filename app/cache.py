"""Redis cache wrapper for token blacklist and rate limiting"""
import redis
import json
from typing import Optional, Any
from datetime import datetime, timedelta, timezone
from app.config import settings
from utils import logger



# Redis connection (lazy initialized)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client (returns None if Redis is unavailable)"""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_keepalive=True
        )
        # Test connection
        _redis_client.ping()
        logger.info("Redis client initialized successfully")
        return _redis_client
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Using in-memory fallback.")
        _redis_client = None
        return None


class TokenBlacklist:
    """Token blacklist management with Redis fallback"""
    
    _in_memory_blacklist = set()
    
    @staticmethod
    def add(token: str, ttl_seconds: int = 604800) -> None:
        """Add token to blacklist with TTL"""
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                redis_client.setex(
                    f"blacklist:token:{token}",
                    ttl_seconds,
                    "1"
                )
            except Exception as e:
                logger.warning(f"Redis blacklist add failed: {e}. Using in-memory.")
                TokenBlacklist._in_memory_blacklist.add(token)
        else:
            TokenBlacklist._in_memory_blacklist.add(token)
    
    @staticmethod
    def is_blacklisted(token: str) -> bool:
        """Check if token is blacklisted"""
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                return redis_client.exists(f"blacklist:token:{token}") > 0
            except Exception as e:
                logger.warning(f"Redis blacklist check failed: {e}. Using in-memory.")
                return token in TokenBlacklist._in_memory_blacklist
        else:
            return token in TokenBlacklist._in_memory_blacklist


class RateLimiter:
    """Rate limiter with Redis fallback"""
    
    _in_memory_buckets = {}
    
    @staticmethod
    def is_allowed(key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit"""
        redis_client = get_redis_client()
        redis_key = f"ratelimit:{key}"
        
        if redis_client:
            try:
                current = redis_client.incr(redis_key)
                if current == 1:
                    redis_client.expire(redis_key, window_seconds)
                return current <= max_requests
            except Exception as e:
                logger.warning(f"Redis rate limit check failed: {e}. Using in-memory.")
                return RateLimiter._in_memory_check(key, max_requests, window_seconds)
        else:
            return RateLimiter._in_memory_check(key, max_requests, window_seconds)
    
    @staticmethod
    def _in_memory_check(key: str, max_requests: int, window_seconds: int) -> bool:
        """In-memory rate limit fallback"""
        import time
        now = time.time()
        
        if key not in RateLimiter._in_memory_buckets:
            RateLimiter._in_memory_buckets[key] = {
                "count": 1,
                "window_start": now,
                "window_seconds": window_seconds
            }
            return True
        
        bucket = RateLimiter._in_memory_buckets[key]
        if now - bucket["window_start"] >= bucket["window_seconds"]:
            bucket["count"] = 1
            bucket["window_start"] = now
            return True
        
        bucket["count"] += 1
        return bucket["count"] <= max_requests
    
    @staticmethod
    def get_remaining(key: str, max_requests: int) -> int:
        """Get remaining requests in current window"""
        redis_client = get_redis_client()
        redis_key = f"ratelimit:{key}"
        
        if redis_client:
            try:
                current = redis_client.get(redis_key)
                if current is None:
                    return max_requests
                return max(0, max_requests - int(current))
            except Exception:
                return max_requests
        else:
            if key not in RateLimiter._in_memory_buckets:
                return max_requests
            return max(0, max_requests - RateLimiter._in_memory_buckets[key]["count"])


class SessionStore:
    """Session storage with Redis fallback"""
    
    _in_memory_store = {}
    
    @staticmethod
    def set(key: str, data: Any, ttl_seconds: int = 3600) -> None:
        """Store session data"""
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                redis_client.setex(
                    f"session:{key}",
                    ttl_seconds,
                    json.dumps(data)
                )
            except Exception as e:
                logger.warning(f"Redis session set failed: {e}. Using in-memory.")
                SessionStore._in_memory_store[key] = {
                    "data": data,
                    "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
                }
        else:
            SessionStore._in_memory_store[key] = {
                "data": data,
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            }
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Retrieve session data"""
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                data = redis_client.get(f"session:{key}")
                return json.loads(data) if data else None
            except Exception as e:
                logger.warning(f"Redis session get failed: {e}. Using in-memory.")
                return SessionStore._in_memory_get(key)
        else:
            return SessionStore._in_memory_get(key)
    
    @staticmethod
    def _in_memory_get(key: str) -> Optional[Any]:
        """In-memory session retrieval"""
        if key not in SessionStore._in_memory_store:
            return None
        
        session = SessionStore._in_memory_store[key]
        if datetime.now(timezone.utc) >= session["expires_at"]:
            del SessionStore._in_memory_store[key]
            return None
        
        return session["data"]
    
    @staticmethod
    def delete(key: str) -> None:
        """Delete session data"""
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                redis_client.delete(f"session:{key}")
            except Exception:
                pass
        
        SessionStore._in_memory_store.pop(key, None)
