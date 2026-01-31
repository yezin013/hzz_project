from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os

# Import Routers
from app.api.hansang import router as hansang_router
from app.api.cocktail import router as cocktail_router

# OpenTelemetry (Conditional Import for EKS)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    ENABLE_OTEL = True
except ImportError:
    ENABLE_OTEL = False
    print("OpenTelemetry packages not found. Skipping instrumentation (Running in Lambda?).")

# OpenTelemetry 초기화
def init_opentelemetry():
    if not ENABLE_OTEL:
        return

    """OpenTelemetry 초기화"""
    try:
        service_name = os.getenv("OTEL_SERVICE_NAME", "jumak-backend-recommend")
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "node.ip": os.getenv("NODE_IP", "127.0.0.1"),
        })
        trace.set_tracer_provider(TracerProvider(resource=resource))
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "alloy-alloy-1:4319")
        if otlp_endpoint.startswith("http://"):
            otlp_endpoint = otlp_endpoint.replace("http://", "")
        elif otlp_endpoint.startswith("https://"):
            otlp_endpoint = otlp_endpoint.replace("https://", "")
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        RequestsInstrumentor().instrument()
    except Exception as e:
        print(f"Failed to initialize OpenTelemetry: {e}")

# OpenTelemetry 초기화 (앱 생성 전)
init_opentelemetry()



# Rate Limiter 초기화
limiter = Limiter(key_func=get_remote_address)

# 프로덕션 환경 확인
IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"

app = FastAPI(
    title="Jumak Recommend API",
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json"
)

# FastAPI Instrumentation (앱 생성 후)
if ENABLE_OTEL:
    try:
        FastAPIInstrumentor.instrument_app(app)
    except Exception as e:
        print(f"Failed to instrument FastAPI: {e}")


# Rate Limiter 등록
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Route 등록
app.include_router(hansang_router, prefix="/api/python/hansang", tags=["hansang"])
app.include_router(cocktail_router, prefix="/api/python/cocktail", tags=["cocktail"])

# Health Check
@app.get("/api/python/health")
async def health_check():
    return {"status": "ok", "service": "recommend"}

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
