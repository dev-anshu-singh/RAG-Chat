import logging
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.llm import get_embeddings
from app.core.config import settings
from app.db.database import DocumentMetadata, ProcessingStatus

# Set up basic logging so you can see errors in your Docker console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_document_service(file_path: str, document_id: int, db: Session):
    """
    Background task to process a PDF, chunk it, embed it, and store it in ChromaDB.
    """
    # 1. Fetch the document record and mark it as PROCESSING
    doc_record = db.query(DocumentMetadata).filter(DocumentMetadata.id == document_id).first()
    if not doc_record:
        logger.error(f"Document ID {document_id} not found in database.")
        return

    doc_record.status = ProcessingStatus.PROCESSING
    db.commit()

    try:
        logger.info(f"Starting processing for document ID: {document_id}")

        # 2. Load the PDF using the high-speed PyMuPDFLoader
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()

        # 3. Chunk the document
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        chunks = text_splitter.split_documents(documents)

        # Attach the SQLite document_id to each chunk's metadata
        # (This is a lifesaver later if you only want to search specific documents)
        for chunk in chunks:
            chunk.metadata["document_id"] = document_id

        # 4. Initialize Gemini Embeddings
        embeddings = get_embeddings()

        # 5. Push chunks and embeddings to ChromaDB
        # Chroma automatically creates the directory if it doesn't exist
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=settings.chroma_persist_dir
        )

        # 6. Mark as COMPLETED and save the chunk count
        doc_record.status = ProcessingStatus.COMPLETED
        doc_record.chunk_count = len(chunks)
        db.commit()

        logger.info(f"Successfully processed and embedded {len(chunks)} chunks for document ID: {document_id}")

    except Exception as e:
        # 7. If anything fails (corrupt PDF, API timeout), catch the error safely
        error_msg = str(e)
        logger.error(f"Failed to process document {document_id}: {error_msg}")

        doc_record.status = ProcessingStatus.FAILED
        doc_record.error_message = error_msg
        db.commit()