from datetime import datetime, timezone
import enum
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# 1. Database Setup
# connect_args={"check_same_thread": False} is strictly required for SQLite in FastAPI
engine = create_engine(
    settings.sqlite_db_path,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Status Enum for strict type checking
class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# 3. The Database Model
class DocumentMetadata(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    chunk_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)

# 4. Dependency for FastAPI Routers
def get_db():
    """
    Creates a database session for a single request and closes it when the request is finished.
    This is standard FastAPI dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5. Initialization Function
def init_db():
    """
    Creates the tables in the SQLite database if they don't already exist.
    We will call this in main.py when the app starts up.
    """
    Base.metadata.create_all(bind=engine)