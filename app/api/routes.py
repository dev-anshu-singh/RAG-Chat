import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.graph.workflow import graph_app
from app.core.config import settings
from app.db.database import get_db, DocumentMetadata, ProcessingStatus
from app.api.schemas import QueryRequest, QueryResponse, DocumentResponse
from app.services.document_processor import process_document_service

router = APIRouter()

os.makedirs(settings.upload_dir, exist_ok=True)


@router.post("/upload")
async def upload_documents(
        background_tasks: BackgroundTasks,
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db)
):
    """
    Accepts up to 20 PDFs in a single call, saves them locally,
    and queues them for background chunking.
    """
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="You can only upload up to 20 documents at a time.")

    uploaded_docs = []

    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF. All files must be PDFs.")

        new_doc = DocumentMetadata(filename=file.filename, status=ProcessingStatus.PENDING)
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        file_path = os.path.join(settings.upload_dir, f"{new_doc.id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        background_tasks.add_task(process_document_service, file_path, new_doc.id)

        uploaded_docs.append({"filename": file.filename, "document_id": new_doc.id})

    return {
        "message": f"{len(files)} document(s) uploaded successfully and are currently processing.",
        "documents": uploaded_docs
    }


@router.get("/metadata", response_model=List[DocumentResponse])
def get_metadata(db: Session = Depends(get_db)):
    documents = db.query(DocumentMetadata).all()
    return documents


@router.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    thread_id = request.thread_id or str(uuid.uuid4())

    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph_app.invoke({"question": request.question}, config=config)
        return QueryResponse(
            answer=result["answer"],
            thread_id=thread_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))