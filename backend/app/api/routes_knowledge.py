import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional

from ..core.config import settings
from ..knowledge.index_service import rebuild_index, is_index_built, get_index_size
from ..knowledge.retrieval_service import search_similar_reports, generate_advise

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/status")
async def api_knowledge_status() -> Dict[str, Any]:
    if not settings.KNOWLEDGE_ENABLED:
        return {"enabled": False, "index_built": False, "index_size": 0}
    return {
        "enabled": True,
        "index_built": is_index_built(),
        "index_size": get_index_size(),
        "auto_index": settings.KNOWLEDGE_AUTO_INDEX,
    }


@router.post("/rebuild")
async def api_rebuild_knowledge() -> Dict[str, Any]:
    if not settings.KNOWLEDGE_ENABLED:
        raise HTTPException(status_code=403, detail="Knowledge base is disabled")
    count = rebuild_index()
    return {"indexed": count, "success": True}


@router.post("/search")
async def api_search(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not settings.KNOWLEDGE_ENABLED:
        raise HTTPException(status_code=403, detail="Knowledge base is disabled")
    query = payload.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="需要提供 query")
    max_results = payload.get("max_results", 5)
    review_mode = payload.get("review_mode", None)
    min_score = payload.get("min_score", 0)

    results = search_similar_reports(
        query_text=query,
        max_results=max_results,
        review_mode=review_mode,
        min_score=min_score,
    )
    return {
        "query": query,
        "results_count": len(results),
        "results": [r.to_dict() for r in results],
    }


@router.post("/advise")
async def api_advise(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not settings.KNOWLEDGE_ENABLED:
        raise HTTPException(status_code=403, detail="Knowledge base is disabled")
    query = payload.get("query", "")
    max_results = payload.get("max_results", 5)
    review_mode = payload.get("review_mode", None)

    result = generate_advise(
        query_text=query,
        max_results=max_results,
        review_mode=review_mode,
    )
    return result.to_dict()
