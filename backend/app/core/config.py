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
    KNOWLEDGE_COLLECTION: str = "knowledge_base"
    ANALYTICS_COLLECTION: str = "analytics"

    JWT_SECRET_KEY: str = ""

    JWT_ALGORITHM: str = "HS256"

    GOOGLE_API_KEY: str = ""

    VECTOR_DB_PATH: str = "./vectorstore"

    class Config:
        env_file = ".env"


settings = Settings()
