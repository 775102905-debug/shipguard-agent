import uvicorn
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes_review import router as review_router

app = FastAPI(
    title="AI Delivery Inspector",
    description="AI 项目交付审查系统 — 自动审查 AI 项目源码的交付完整性、安全风险和文档质量",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "AI Delivery Inspector API", "version": "0.2.0"}


@app.get("/health")
async def health():
    return {"status": "ok", "llm_review_enabled": settings.LLM_REVIEW_ENABLED, "metrics_enabled": settings.METRICS_ENABLED}


if settings.METRICS_ENABLED:
    from app.observability.metrics import get_metrics

    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics():
        return get_metrics()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time-Seconds"] = str(round(process_time, 3))
    return response


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
