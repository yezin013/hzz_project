"""
실시간 검색어 통계를 Redis에 저장하는 함수
- Redis Sorted Set을 사용한 자동 정렬 및 랭킹
- 동적 TTL: 기본 1시간, 재검색 시 30분씩 연장
"""
from datetime import datetime
import redis
import os
from typing import List, Dict, Optional


def get_redis_client():
    """Get Redis client for search stats storage"""
    try:
        return redis.StrictRedis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
    except Exception as e:
        print(f"❌ Redis connection failed for search stats: {e}")
        return None


async def save_search_query(query: str, drink_id: int = None):
    """
    검색어를 Redis Sorted Set에 저장 (술 이름과 drink_id 함께 저장)
    
    TTL 전략:
    - 기본 TTL: 1시간 (3600초)
    - 재검색 시: 현재 TTL + 30분 (1800초) 연장
    """
    r = get_redis_client()
    if not r:
        print("⚠️ Redis unavailable, search query not saved")
        return
    
    try:
        # 검색어를 정규화 (공백 제거)
        normalized_query = query.strip()
        
        # 오늘 날짜 (YYYYMMDD 형식)
        today = datetime.now().strftime("%Y%m%d")
        
        # Redis Key: search:ranking:{YYYYMMDD}
        ranking_key = f"search:ranking:{today}"
        
        # Sorted Set Member: "{query}:{drink_id}"
        if drink_id:
            member = f"{normalized_query}:{drink_id}"
        else:
            member = normalized_query
        
        # 1. 검색어 카운트 증가 (Sorted Set의 score 증가)
        r.zincrby(ranking_key, 1, member)
        
        # 2. TTL 동적 연장
        current_ttl = r.ttl(ranking_key)
        
        if current_ttl == -1:  # TTL이 설정되지 않은 경우 (처음 생성)
            r.expire(ranking_key, 3600)  # 1시간 (3600초)
            print(f"✅ Search query saved: {normalized_query} (drink_id: {drink_id}) | TTL: 1 hour")
        elif current_ttl > 0:  # TTL이 설정된 경우 (재검색)
            new_ttl = current_ttl + 1800  # 현재 TTL + 30분 (1800초)
            r.expire(ranking_key, new_ttl)
            print(f"✅ Search query updated: {normalized_query} (drink_id: {drink_id}) | TTL extended: {new_ttl}s")
        else:  # 키가 만료되었거나 없는 경우
            r.expire(ranking_key, 3600)  # 기본 1시간
            print(f"✅ Search query saved: {normalized_query} (drink_id: {drink_id}) | TTL: 1 hour")
            
    except Exception as e:
        print(f"❌ Error saving search query to Redis: {e}")


async def get_top_searches(limit: int = 10) -> List[Dict]:
    """
    오늘 실시간 검색어 Top N 반환 (drink_id 포함)
    Redis Sorted Set에서 즉시 조회
    """
    r = get_redis_client()
    if not r:
        print("⚠️ Redis unavailable, returning empty list")
        return []
    
    try:
        # 오늘 날짜
        today = datetime.now().strftime("%Y%m%d")
        ranking_key = f"search:ranking:{today}"
        
        # Sorted Set에서 Top N 조회 (score 내림차순)
        # ZREVRANGE: 높은 score부터 조회
        top_results = r.zrevrange(ranking_key, 0, limit - 1, withscores=True)
        
        results = []
        for member, score in top_results:
            # Member 파싱: "{query}:{drink_id}" 또는 "{query}"
            if ":" in member:
                parts = member.rsplit(":", 1)  # 마지막 ':'로 분리
                query_text = parts[0]
                try:
                    drink_id_val = int(parts[1])
                except (ValueError, IndexError):
                    drink_id_val = None
            else:
                query_text = member
                drink_id_val = None
            
            results.append({
                "query": query_text,
                "count": int(score),
                "drink_id": drink_id_val
            })
        
        return results
        
    except Exception as e:
        print(f"❌ Error getting top searches from Redis: {e}")
        return []
