"""
Lambda Handler for Content Service
FastAPI를 Mangum으로 래핑하여 AWS Lambda에서 실행

Secrets Manager 통합:
- Lambda 시작 시 시크릿을 환경변수로 로드
- MongoDB 연결은 첫 요청 시 lazy initialization
"""

# 1. 먼저 시크릿 로드 (다른 모듈 import 전에)
try:
    from app.utils.secrets import load_secrets_to_env
    load_secrets_to_env()
    print("✅ Secrets loaded to environment")
except Exception as e:
    print(f"⚠️ Failed to load secrets: {e}")

# 2. FastAPI 앱 import (시크릿 로드 후)
from mangum import Mangum
from main import app

# 3. Lambda 핸들러
# lifespan="auto"로 설정하면 Mangum이 startup/shutdown 이벤트 처리
# MongoDB 연결은 FastAPI의 lifespan에서 처리됨
handler = Mangum(app, lifespan="auto")
