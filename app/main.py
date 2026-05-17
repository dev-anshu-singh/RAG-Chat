from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.database import init_db
from app.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="RAG Document Ingestion & Query API",
    description="Intern Assignment: Production-ready stateful RAG pipeline utilizing LangGraph, ChromaDB, Cohere Reranking, and Gemini.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "message": "The RAG API is running smoothly.",
        "documentation_url": "/docs"
    }