import os
import redis
import json
from datetime import datetime

def get_redis_client():
    """Get Redis client for metrics logging"""
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

def log_chatbot_metrics(
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    latency_seconds: float,
    model: str,
    success: bool,
    endpoint: str
):
    """Log chatbot metrics to Redis"""
    try:
        r = get_redis_client()
        if not r:
            return
        
        metric_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "latency_seconds": latency_seconds,
            "model": model,
            "success": success,
            "endpoint": endpoint
        }
        
        # Push to Redis list
        r.lpush("chatbot:metrics", json.dumps(metric_data))
        r.ltrim("chatbot:metrics", 0, 999)  # Keep last 1000 records
        
    except Exception as e:
        print(f"⚠️ Metrics logging failed: {e}")
