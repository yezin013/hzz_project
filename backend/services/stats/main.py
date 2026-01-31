import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongodb import close_mongo_connection, connect_to_mongo # metrics might use mongo? No, uses redis. Weather uses redis/OWM.
# But keep generic setup just in case. Actually, metrics uses REDIS. Weather uses REDIS.
# So Mongo is not strictly needed unless one of them uses it.
# Metrics uses `utils.metrics` -> `api.metrics`. Let's check imports.
# Utils metrics: uses Redis.
# Utils weather: uses Redis.
# Stats ranking: uses Redis.
# So Mongo connection is NOT needed for backend-stats!

from app.api.weather import router as weather_router
from app.api.metrics import router as metrics_router
from app.api.stats_ranking import router as ranking_router

# 프로덕션 환경 확인
IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"

app = FastAPI(
    title="Jumak Stats Service",
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json"
)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://hanzanzu.cloud",
    "https://www.hanzanzu.cloud",
    "https://serverless.hanzanzu.cloud",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route 등록
# 1. Weather (Moved from Info/Core)
app.include_router(weather_router, prefix="/api/python/weather", tags=["weather"])

# 2. Metrics (Moved from Chatbot)
app.include_router(metrics_router, prefix="/api/python/chatbot/metrics", tags=["metrics"])

# 3. Search Ranking (Moved from Search)
app.include_router(ranking_router, prefix="/api/python/search", tags=["ranking"]) 
# Access via /api/python/search/top-searches

@app.get("/api/python/health")
async def health_check():
    return {"status": "ok", "service": "stats"}
