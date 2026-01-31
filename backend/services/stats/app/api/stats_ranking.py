from fastapi import APIRouter
from app.utils.search_stats import get_top_searches

router = APIRouter()

@router.get("/top-searches")
async def get_top_searches_endpoint(limit: int = 10):
    """오늘 하루 동안 가장 많이 검색된 검색어 Top N 반환"""
    results = await get_top_searches(limit)
    return {"top_searches": results}
