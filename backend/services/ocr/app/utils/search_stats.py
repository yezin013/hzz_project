import redis
import os
from datetime import datetime

def get_redis_client():
    """Get Redis client for search stats"""
    try:
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_connect_timeout=2
        )
        client.ping()
        return client
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        return None

def save_search_query(query: str):
    """Save search query to Redis"""
    try:
        r = get_redis_client()
        if not r:
            return
        
        # Increment search count
        r.zincrby("search:queries", 1, query)
        
        # Save with timestamp
        r.zadd(f"search:history", {query: datetime.utcnow().timestamp()})
        
    except Exception as e:
        print(f"⚠️ Search stats save failed: {e}")

def get_top_searches(limit: int = 10):
    """Get top search queries"""
    try:
        r = get_redis_client()
        if not r:
            return []
        
        # Get top queries with scores
        top_queries = r.zrevrange("search:queries", 0, limit - 1, withscores=True)
        
        return [{"query": q, "count": int(score)} for q, score in top_queries]
        
    except Exception as e:
        print(f"⚠️ Get top searches failed: {e}")
        return []
