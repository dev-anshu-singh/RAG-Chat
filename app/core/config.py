from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    gemini_api_key: str
    cohere_api_key: str

    langsmith_tracing_v2: str
    langsmith_endpoint: str
    langsmith_api_key: str
    langsmith_project: str

    chunk_size: int = 2000
    chunk_overlap: int = 200

    llm_model: str = "gemini-2.5-flash"
    gemini_embedding_model : str = "gemini-embedding-001"
    sqlite_db_path: str = "sqlite:///./data/metadata.db"
    chroma_persist_dir: str = "./data/chroma_db"
    upload_dir: str = "./data/uploads"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()