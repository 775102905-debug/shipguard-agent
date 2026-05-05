import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes_review import router as review_router

app = FastAPI(
    title="AI Delivery Inspector",
    description="AI 项目交付审查系统 — 自动审查 AI 项目源码的交付完整性、安全风险和文档质量",
    version="0.1.0",
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
    return {"message": "AI Delivery Inspector API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
