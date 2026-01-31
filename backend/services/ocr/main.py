from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.ocr import router as ocr_router
import os

# 프로덕션 환경 확인
IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"

app = FastAPI(
    title="Jumak OCR Service",
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

# OCR 라우터만 등록
app.include_router(ocr_router, prefix="/api/python/ocr", tags=["ocr"])

@app.get("/api/python/ocr/health")
async def health_check():
    return {"status": "ok", "service": "ocr"}
