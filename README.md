# RAG Document Assistant

A production-oriented Retrieval-Augmented Generation (RAG) application built for the LLM Intern Assignment. The system lets users upload PDF documents, processes them into semantic chunks, stores those chunks in a persistent ChromaDB vector database, and answers questions using retrieved document context with a Gemini LLM.

The application includes a FastAPI REST backend, a Streamlit frontend, SQLite metadata storage, LangGraph conversational memory, Cohere reranking, automated tests, and Docker Compose deployment.

## Project Overview

This project implements an end-to-end document question-answering pipeline:

1. Users upload one or more PDF files through the REST API or Streamlit UI.
2. The backend stores document metadata in SQLite and saves uploaded files under `data/uploads`.
3. FastAPI background tasks extract PDF text with PyMuPDF, split content into overlapping chunks, and embed those chunks with Google Gemini embeddings.
4. Chunks are stored in ChromaDB under `data/chroma_db`.
5. User questions are routed through a LangGraph workflow.
6. The retriever first fetches the top 30 semantically similar chunks from ChromaDB.
7. Cohere Rerank filters those candidates to the top 6 most relevant chunks.
8. Gemini generates a concise answer using the retrieved context and the active chat history.

The design separates ingestion, retrieval, response generation, metadata persistence, and UI concerns so the project can be run locally, tested automatically, or deployed with containers.

## Assignment Coverage

| Requirement | Implementation |
| --- | --- |
| Upload documents | `POST /upload` accepts PDF uploads and supports up to 20 files per request. |
| Large document processing | PyMuPDF extracts PDF pages and LangChain splits text into configurable chunks. |
| Chunking | `RecursiveCharacterTextSplitter` with default `CHUNK_SIZE=2000` and `CHUNK_OVERLAP=200`. |
| Embeddings | Gemini embedding model configured through `GEMINI_EMBEDDING_MODEL`. |
| Vector database | Persistent ChromaDB stored in `data/chroma_db`. |
| RAG querying | `POST /query` retrieves relevant chunks and passes them to the LLM. |
| Reranking | Cohere `rerank-english-v3.0` reranks retrieved chunks for higher precision. |
| REST API | FastAPI backend with upload, query, metadata, root, and Swagger docs endpoints. |
| Metadata database | SQLite with SQLAlchemy ORM tracks filename, upload date, status, chunk count, and errors. |
| Containerization | Dockerfiles for backend/frontend and `docker-compose.yml` for both services. |
| Testing | Pytest suite covers root, metadata, upload validation, query validation, and mocked query handling. |
| Documentation | This README includes setup, configuration, API usage, testing, and deployment details. |

## Key Features

- Batch PDF upload with validation for PDF-only files and a maximum of 20 documents per request.
- Non-blocking background ingestion so upload requests return while document processing continues.
- Scanned or image-only PDF protection by failing documents that produce no extractable text chunks.
- Persistent document metadata with processing states: `pending`, `processing`, `completed`, and `failed`.
- Rate-limit-aware embedding writes using small batches and exponential backoff for `429` or `RESOURCE_EXHAUSTED` errors.
- Two-stage retrieval: ChromaDB semantic search for high recall, followed by Cohere reranking for precision.
- Stateful chat memory using LangGraph `MemorySaver` and a reusable `thread_id`.
- Streamlit UI with tabs for uploading PDFs, viewing processing status, and chatting with documents.
- Docker Compose setup for local or cloud VM deployment.

## Technology Stack

- Backend: FastAPI, Python 3.11, Uvicorn
- Frontend: Streamlit
- LLM: Google Gemini via `langchain-google-genai`
- Embeddings: Google Gemini embeddings
- Reranking: Cohere Rerank API
- Vector database: ChromaDB
- Metadata database: SQLite with SQLAlchemy ORM
- Orchestration: LangChain, LangGraph
- PDF processing: PyMuPDF
- Testing: Pytest, FastAPI TestClient, HTTPX
- Deployment: Docker, Docker Compose

## Repository Structure

```text
.
|-- app/
|   |-- api/
|   |   |-- routes.py          # FastAPI endpoints
|   |   `-- schemas.py         # Request/response models
|   |-- core/
|   |   |-- config.py          # Environment-based settings
|   |   `-- llm.py             # Gemini LLM and embedding clients
|   |-- db/
|   |   `-- database.py        # SQLite engine, ORM model, DB dependency
|   |-- graph/
|   |   |-- nodes.py           # Retrieve and generate workflow nodes
|   |   |-- state.py           # LangGraph state schema
|   |   `-- workflow.py        # LangGraph workflow setup
|   |-- retrieval/
|   |   `-- retriever.py       # Chroma retriever and Cohere reranker
|   |-- services/
|   |   `-- document_processor.py
|   `-- main.py                # FastAPI application entrypoint
|-- frontend/
|   |-- frontend.py            # Streamlit UI
|   `-- Dockerfile             # Frontend container
|-- tests/
|   `-- test_api.py            # Automated API tests
|-- data/                      # Runtime data: uploads, SQLite DB, Chroma DB
|-- Dockerfile                 # Backend container
|-- docker-compose.yml
|-- requirements.txt
`-- README.md
```

## Prerequisites

- Python 3.11+
- Docker and Docker Compose, for containerized deployment
- Google Gemini API key
- Cohere API key
- Optional LangSmith API key, if tracing is enabled

## Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
COHERE_API_KEY=your_cohere_api_key

LANGSMITH_TRACING_V2=false
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=rag-document-assistant
```

The following settings also have defaults in `app/core/config.py` and can be overridden through environment variables:

```env
CHUNK_SIZE=2000
CHUNK_OVERLAP=200
LLM_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
SQLITE_DB_PATH=sqlite:///./data/metadata.db
CHROMA_PERSIST_DIR=./data/chroma_db
UPLOAD_DIR=./data/uploads
```

For the frontend, `API_BASE_URL` controls the backend URL. Local development defaults to `http://127.0.0.1:8000`; Docker Compose sets it to `http://backend:8000`.

## Local Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Create the `.env` file as shown above.

4. Start the FastAPI backend:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

5. In a second terminal, start the Streamlit frontend:

```bash
streamlit run frontend/frontend.py
```

6. Open:

- Frontend: `http://localhost:8501`
- API docs: `http://localhost:8000/docs`
- API root: `http://localhost:8000/`

## Docker Compose Deployment

Build and start both services:

```bash
docker compose up --build
```

Then open:

- Streamlit frontend: `http://localhost:8501`
- FastAPI backend: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

Runtime data is mounted through:

```yaml
./data:/code/data
```

This keeps uploaded PDFs, SQLite metadata, and ChromaDB vector data available across backend container restarts.

To stop the stack:

```bash
docker compose down
```

## API Usage

### Health Check

```http
GET /
```

Response:

```json
{
  "message": "The RAG API is running smoothly.",
  "documentation_url": "/docs"
}
```

### Upload Documents

```http
POST /upload
Content-Type: multipart/form-data
```

Form field:

- `files`: one or more PDF files, up to 20 documents per request

Example with curl:

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf"
```

Example response:

```json
{
  "message": "2 document(s) uploaded successfully and are currently processing.",
  "documents": [
    {
      "filename": "document1.pdf",
      "document_id": 1
    },
    {
      "filename": "document2.pdf",
      "document_id": 2
    }
  ]
}
```

### View Document Metadata

```http
GET /metadata
```

Example response:

```json
[
  {
    "id": 1,
    "filename": "document1.pdf",
    "upload_date": "2026-05-18T04:30:00.000000",
    "status": "completed",
    "chunk_count": 42,
    "error_message": null
  }
]
```

### Query Documents

```http
POST /query
Content-Type: application/json
```

Request body:

```json
{
  "question": "What are the main conclusions in the uploaded document?",
  "thread_id": "optional-existing-thread-id"
}
```

If `thread_id` is omitted, the backend creates a new conversation thread. Reuse the returned `thread_id` for follow-up questions.

Example with curl:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Summarize the uploaded documents in five points.\"}"
```

Example response:

```json
{
  "answer": "The uploaded documents primarily discuss...",
  "thread_id": "d57b651e-0c5e-4a41-a3f1-ec6c6d35e29f"
}
```

## RAG Pipeline Details

### Ingestion

- Endpoint: `POST /upload`
- Saves files to `data/uploads`
- Creates a `DocumentMetadata` row with `pending` status
- Schedules `process_document_service` as a FastAPI background task
- Updates status to `processing`, `completed`, or `failed`

### Processing

- Loads PDFs with `PyMuPDFLoader`
- Splits extracted text using `RecursiveCharacterTextSplitter`
- Adds `document_id` to chunk metadata
- Rejects documents where no text chunks can be extracted
- Embeds chunks with Gemini embeddings
- Inserts chunks into ChromaDB in batches of 15
- Retries rate-limited embedding calls with exponential backoff

### Retrieval and Generation

- ChromaDB retrieves the top 30 semantically similar chunks.
- Cohere Rerank compresses those candidates to the top 6 chunks.
- LangGraph passes retrieved context and chat history to Gemini.
- Gemini answers with `temperature=0` for deterministic, context-grounded responses.

## Testing

Run the automated test suite:

```bash
pytest
```

The tests currently validate:

- Root endpoint response
- Metadata endpoint shape
- Invalid non-PDF upload rejection
- More than 20 uploaded files rejection
- Query request validation
- Successful query flow with the LangGraph invocation mocked

The mocked query test avoids live LLM calls, so it does not consume Gemini or Cohere credits.

## Configuring Different LLM Providers

The current implementation is wired for:

- Gemini chat model in `app/core/llm.py`
- Gemini embeddings in `app/core/llm.py`
- Cohere reranking in `app/retrieval/retriever.py`

To use another provider such as OpenAI, Azure OpenAI, Anthropic, or a local REST-based model:

1. Add the required provider package to `requirements.txt`.
2. Add provider-specific environment variables in `app/core/config.py`.
3. Replace `get_chat_llm()` in `app/core/llm.py` with the new chat model client.
4. Replace `get_embeddings()` if the vector embeddings provider changes.
5. Keep the returned objects compatible with LangChain's chat model and embedding interfaces.
6. Rebuild the containers with `docker compose up --build`.

For example, replacing Gemini with OpenAI would typically involve using `ChatOpenAI` and `OpenAIEmbeddings`, then adding an `OPENAI_API_KEY` environment variable.

## Deployment Notes

- The project can run locally on a laptop or on a cloud VM with Docker Compose.
- For AWS, GCP, or Azure, provision a VM/container host, copy the repository, create `.env`, and run `docker compose up --build -d`.
- Persist the `data` directory using a mounted disk or managed volume if long-term document storage is required.
- Do not commit `.env`, `data/`, uploaded PDFs, SQLite databases, or ChromaDB files. They are intentionally ignored by `.gitignore`.
- API keys should be stored in environment variables or cloud secret managers.

## Known Operational Considerations

- The API validates the 20-document upload limit and PDF file extensions.
- Very large PDFs depend on extraction quality, embedding API quota, and available memory.
- Image-only scanned PDFs require OCR before upload; this project rejects PDFs that produce no text chunks.
- In-memory LangGraph chat history is reset when the backend process restarts.
- SQLite is suitable for local assignment/demo use. For production multi-instance deployments, replace it with PostgreSQL or another managed database.

## Useful Commands

```bash
# Run backend locally
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Run frontend locally
streamlit run frontend/frontend.py

# Run tests
pytest

# Start full Docker stack
docker compose up --build

# Stop Docker stack
docker compose down
```
