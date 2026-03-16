from fastapi import APIRouter, HTTPException

from ...schemas.rag import IndexResponse, QueryRequest, QueryResponse
from ...services.rag_service import RagService, RagServiceError

router = APIRouter(prefix="/v1/rag", tags=["rag"])


@router.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    try:
        result = RagService.query(payload.question, payload.question_type)
    except RagServiceError as e:
        raise HTTPException(status_code=500, detail={"code": "RAG_QUERY_ERROR", "message": str(e)})

    retrieval_debug = result.get("retrieval_debug") if payload.include_debug else None
    return QueryResponse(
        answer=result.get("answer", ""),
        refusal=bool(result.get("refusal", False)),
        reason=result.get("reason", ""),
        sources=result.get("sources", []),
        gate=result.get("gate"),
        retrieval_debug=retrieval_debug,
    )


@router.post("/index", response_model=IndexResponse)
def index() -> IndexResponse:
    try:
        chunks = RagService.build_index()
    except RagServiceError as e:
        code = "INDEX_BUILD_IN_PROGRESS" if str(e) == "INDEX_BUILD_IN_PROGRESS" else "RAG_INDEX_ERROR"
        status = 409 if code == "INDEX_BUILD_IN_PROGRESS" else 500
        raise HTTPException(status_code=status, detail={"code": code, "message": str(e)})
    return IndexResponse(chunks=chunks)
