"""
Chatbot metrics collection and aggregation using Redis.
Tracks token usage, latency, and costs for AWS Bedrock Nova.
"""

import redis
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def get_redis_client():
    """Get Redis client for metrics storage"""
    try:
        return redis.StrictRedis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
    except Exception as e:
        print(f"❌ Redis connection failed for metrics: {e}")
        return None


def log_chatbot_metrics(
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    latency_seconds: float,
    model: str = "amazon.nova-lite-v1:0",
    success: bool = True,
    endpoint: str = "chat"
):
    """
    Log chatbot request metrics to Redis.
    - Individual logs: 7-day retention
    - Daily aggregates: 30-day retention
    """
    r = get_redis_client()
    if not r:
        return  # Fail silently if Redis unavailable
    
    try:
        timestamp = datetime.utcnow()
        today = timestamp.strftime('%Y-%m-%d')
        
        # 1. Store individual log (7 days)
        log_key = f"chatbot:log:{timestamp.strftime('%Y%m%d%H%M%S%f')}"
        log_data = {
            "timestamp": timestamp.isoformat(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "latency_seconds": latency_seconds,
            "model": model,
            "success": success,
            "endpoint": endpoint
        }
        r.setex(log_key, 86400 * 7, json.dumps(log_data))
        
        # 2. Update daily aggregates (30 days retention)
        stats_key = f"chatbot:stats:{today}"
        r.hincrby(stats_key, "total_requests", 1)
        r.hincrby(stats_key, "total_tokens", total_tokens)
        r.hincrby(stats_key, "input_tokens", input_tokens)
        r.hincrby(stats_key, "output_tokens", output_tokens)
        r.hincrbyfloat(stats_key, "total_latency", latency_seconds)
        
        if success:
            r.hincrby(stats_key, "successful_requests", 1)
        else:
            r.hincrby(stats_key, "failed_requests", 1)
        
        # Set expiry on stats key (30 days)
        r.expire(stats_key, 86400 * 30)
        
        print(f"📊 Metrics logged: {total_tokens} tokens, {latency_seconds:.2f}s")
        
    except Exception as e:
        print(f"⚠️ Failed to log metrics: {e}")


def get_daily_summary(date: Optional[str] = None) -> Dict:
    """
    Get metrics summary for a specific date.
    If date is None, returns today's metrics.
    """
    r = get_redis_client()
    if not r:
        return {"error": "Redis unavailable"}
    
    if date is None:
        date = datetime.utcnow().strftime('%Y-%m-%d')
    
    stats_key = f"chatbot:stats:{date}"
    stats = r.hgetall(stats_key)
    
    if not stats:
        return {
            "date": date,
            "total_requests": 0,
            "total_tokens": 0,
            "avg_tokens_per_request": 0,
            "avg_latency_seconds": 0,
            "estimated_cost_usd": 0,
            "success_rate": 0
        }
    
    total_requests = int(stats.get("total_requests", 0))
    total_tokens = int(stats.get("total_tokens", 0))
    input_tokens = int(stats.get("input_tokens", 0))
    output_tokens = int(stats.get("output_tokens", 0))
    total_latency = float(stats.get("total_latency", 0))
    successful = int(stats.get("successful_requests", 0))
    
    # Calculate cost (Nova Lite pricing)
    # Input: $0.00006 per 1K tokens
    # Output: $0.00024 per 1K tokens
    input_cost = (input_tokens / 1000) * 0.00006
    output_cost = (output_tokens / 1000) * 0.00024
    total_cost = input_cost + output_cost
    
    return {
        "date": date,
        "total_requests": total_requests,
        "successful_requests": successful,
        "failed_requests": int(stats.get("failed_requests", 0)),
        "success_rate": (successful / total_requests * 100) if total_requests > 0 else 0,
        "total_tokens": total_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "avg_tokens_per_request": total_tokens / total_requests if total_requests > 0 else 0,
        "avg_latency_seconds": total_latency / total_requests if total_requests > 0 else 0,
        "estimated_cost_usd": round(total_cost, 6)
    }


def get_metrics_history(days: int = 7) -> List[Dict]:
    """
    Get metrics for the last N days.
    Returns list of daily summaries.
    """
    history = []
    today = datetime.utcnow()
    
    for i in range(days):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        summary = get_daily_summary(date)
        history.append(summary)
    
    return history


def get_system_status() -> Dict:
    """
    Check system health: Bedrock and Redis availability.
    """
    import time
    start_time = getattr(get_system_status, '_start_time', time.time())
    if not hasattr(get_system_status, '_start_time'):
        get_system_status._start_time = start_time
    
    status = {
        "bedrock_available": True,
        "redis_available": False,
        "last_error": None,
        "uptime_seconds": int(time.time() - start_time)
    }
    
    # Check Redis
    r = get_redis_client()
    if r:
        try:
            r.ping()
            status["redis_available"] = True
        except Exception as e:
            status["redis_available"] = False
            status["last_error"] = f"Redis: {str(e)}"
    
    # Check Bedrock (try to import)
    try:
        import boto3
        status["bedrock_available"] = True
    except Exception as e:
        status["bedrock_available"] = False
        status["last_error"] = f"Bedrock: {str(e)}"
    
    return status


def log_error(error_type: str, message: str):
    """
    Log error to Redis for dashboard display.
    Stores last 100 errors with 24-hour TTL.
    """
    r = get_redis_client()
    if not r:
        return
    
    try:
        error_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": error_type,
            "message": message
        }
        
        # Add to list (keeping last 100)
        key = "chatbot:errors"
        r.lpush(key, json.dumps(error_log))
        r.ltrim(key, 0, 99)  # Keep only 100 most recent
        r.expire(key, 86400)  # 24 hour TTL
        
        print(f"🚨 Error logged: [{error_type}] {message}")
    except Exception as e:
        print(f"Failed to log error: {e}")


def get_recent_errors(limit: int = 20) -> List[Dict]:
    """
    Get recent error logs from Redis.
    """
    r = get_redis_client()
    if not r:
        return []
    
    try:
        key = "chatbot:errors"
        error_logs = r.lrange(key, 0, limit - 1)
        
        errors = []
        for log in error_logs:
            try:
                errors.append(json.loads(log))
            except:
                pass
        
        return errors
    except Exception as e:
        print(f"Failed to fetch errors: {e}")
        return []


def get_chatbot_metrics_summary():
    """
    Get chatbot metrics summary (alias for get_daily_summary).
    Returns today's metrics by default.
    """
    return get_daily_summary()

