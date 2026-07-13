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
    UPLOAD_DIRECTORY: str = "storage/uploads/pdfs"

    class Config:
        env_file = ".env"


settings = Settings()
