from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.db.database import ProcessingStatus

class QueryRequest(BaseModel):
    question: str
    # start a new chat or continue an old one by passing the same ID.
    thread_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    thread_id: str

class DocumentResponse(BaseModel):
    id: int
    filename: str
    upload_date: datetime
    status: ProcessingStatus
    chunk_count: int
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)