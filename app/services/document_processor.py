import time
import logging
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from app.core.config import settings
from app.core.llm import get_embeddings
from app.db.database import SessionLocal, DocumentMetadata, ProcessingStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BATCH_SIZE = 15


def embed_with_retry(vectorstore: Chroma, batch: list, retries: int = 5):
    for attempt in range(retries):
        try:
            vectorstore.add_documents(batch)
            return
        except Exception as e:
            # Catch 429 and RESOURCE_EXHAUSTED specifically
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < retries - 1:
                    wait = 15 * (2 ** attempt)
                    logger.warning(f"Rate limited. Retrying in {wait}s... (attempt {attempt + 1}/{retries})")
                    time.sleep(wait)
                else:
                    logger.error(f"Max retries exceeded for this batch. Error: {e}")
                    raise
            else:
                raise


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
            logger.info(f"Starting processing for document ID: {document_id}")

            loader = PyMuPDFLoader(file_path)
            documents = loader.load()

            total_chars = sum(len(doc.page_content) for doc in documents)
            logger.info(f"Loaded {len(documents)} pages, {total_chars} total characters.")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )
            chunks = text_splitter.split_documents(documents)

            for chunk in chunks:
                chunk.metadata["document_id"] = document_id

            total = len(chunks)

            if total == 0:
                raise ValueError(
                    "No text could be extracted from this PDF. "
                    "It may be a scanned/image-based document. "
                    "Please upload a text-based PDF."
                )

            logger.info(f"Total chunks: {total}. Starting batch insertion...")

            embeddings = get_embeddings()

            vectorstore = Chroma(
                embedding_function=embeddings,
                persist_directory=settings.chroma_persist_dir
            )

            for i in range(0, total, BATCH_SIZE):
                batch = chunks[i:i + BATCH_SIZE]
                embed_with_retry(vectorstore, batch)
                logger.info(f"Inserted batch: chunks {i} to {i + len(batch)}.")
                time.sleep(0.7)

            doc_record.status = ProcessingStatus.COMPLETED
            doc_record.chunk_count = total
            db.commit()

            logger.info(f"Successfully finished processing document ID: {document_id}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to process document {document_id}: {error_msg}")
            doc_record.status = ProcessingStatus.FAILED
            doc_record.error_message = error_msg
            db.commit()

    finally:
        db.close()