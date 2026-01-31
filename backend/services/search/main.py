from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.search import router as search_router

import os

# 프로덕션 환경 확인
IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"

app = FastAPI(
    title="Jumak Search Service",
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

# 검색 관련 라우터만 등록
app.include_router(search_router, prefix="/api/python/search", tags=["search"])


@app.get("/api/python/search/health")
async def health_check():
    return {"status": "ok", "service": "search"}
