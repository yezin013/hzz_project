from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.api.board import router as board_router
from app.api.tasting_note import router as note_router
from app.api.favorites import router as favorites_router
import os

# MongoDB lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

# 프로덕션 환경 확인
IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"

app = FastAPI(
    lifespan=lifespan,
    title="Jumak Content Service",
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

# 사용자 콘텐츠 관련 라우터만 등록
app.include_router(board_router, prefix="/api/python/board", tags=["board"])
app.include_router(note_router, prefix="/api/python/notes", tags=["notes"])
app.include_router(favorites_router, prefix="/api/python/favorites", tags=["favorites"])

@app.get("/api/python/content/health")
async def health_check():
    return {"status": "ok", "service": "content"}
