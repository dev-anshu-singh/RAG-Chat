import logging
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from app.core.config import settings
from app.core.llm import get_embeddings
from app.db.database import SessionLocal, DocumentMetadata, ProcessingStatus

logger = logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_document_service(file_path: str, document_id: int):
    db = SessionLocal()
    try:
        doc_record = db.query(DocumentMetadata).filter(DocumentMetadata.id == document_id).first()
        if not doc_record:
            logger.error(f"Document ID {document_id} not found in database.")
            return

        doc_record.status = ProcessingStatus.PROCESSING
        db.commit()

        try:
            loader = PyMuPDFLoader(file_path)
            documents = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )
            chunks = text_splitter.split_documents(documents)

            for chunk in chunks:
                chunk.metadata["document_id"] = document_id

            embeddings = get_embeddings()
            Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=settings.chroma_persist_dir
            )

            doc_record.status = ProcessingStatus.COMPLETED
            doc_record.chunk_count = len(chunks)
            db.commit()

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to process document {document_id}: {error_msg}")
            doc_record.status = ProcessingStatus.FAILED
            doc_record.error_message = error_msg
            db.commit()

    finally:
        db.close()