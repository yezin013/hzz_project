from fastapi import APIRouter
from app.utils.metrics import get_chatbot_metrics_summary

router = APIRouter()

@router.get("/summary")
async def get_metrics_summary():
    """챗봇 메트릭 요약 조회"""
    try:
        summary = get_chatbot_metrics_summary()
        return summary
    except Exception as e:
        return {"error": str(e)}
