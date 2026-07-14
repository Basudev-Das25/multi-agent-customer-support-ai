from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Multi-Agent Customer Support AI"
    APP_VERSION: str = "1.0.0"

    ENVIRONMENT: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DEBUG: bool = True

    MONGODB_URI: str = ""
    DATABASE_NAME: str = "customer_support_ai"

    USERS_COLLECTION: str = "users"
    CONVERSATIONS_COLLECTION: str = "conversations"
    KNOWLEDGE_COLLECTION: str = "knowledge_documents"
    ANALYTICS_COLLECTION: str = "analytics"

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    GOOGLE_API_KEY: str = ""

    VECTOR_DB_PATH: str = "./vectorstore"

    UPLOAD_DIRECTORY: str = "storage/uploads/pdfs"

    MAX_UPLOAD_SIZE_MB: int = 20

    ALLOWED_UPLOAD_TYPES: str = "application/pdf"
    KNOWLEDGE_CHUNKS_COLLECTION: str = "knowledge_chunks"

    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    FAISS_INDEX_PATH: str = "storage/faiss"

    TOP_K_RESULTS: int = 5

    OPENROUTER_API_KEY: str = ""

    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    OPENROUTER_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b:free"

    FAISS_INDEX_NAME: str = "knowledge.index"
    FAISS_MAPPING_NAME: str = "mapping.json"

    OPENROUTER_API_KEY: str = ""

    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    OPENROUTER_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b:free"

    LLM_TIMEOUT_SECONDS: int = 60

    LLM_MAX_TOKENS: int = 1024

    LLM_TEMPERATURE: float = 0.2

    class Config:
        env_file = ".env"


settings = Settings()
