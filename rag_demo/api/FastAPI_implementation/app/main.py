from fastapi import FastAPI

from .api.v1.rag import router as rag_router

app = FastAPI(title="RAG Demo FastAPI", version="0.1.0")
app.include_router(rag_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}
