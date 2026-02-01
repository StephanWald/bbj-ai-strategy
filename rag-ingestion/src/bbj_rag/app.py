"""FastAPI application entrypoint for the BBJ RAG service.

Minimal skeleton -- Plan 02 adds lifespan handler with schema
application, startup summary, and environment validation.
"""

from fastapi import FastAPI

from bbj_rag.health import router as health_router

app = FastAPI(title="BBJ RAG")
app.include_router(health_router)
