from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    database_url: str = "postgresql://isra:isra@localhost:5432/isra"
    llm_model: str = "anthropic/claude-haiku-4.5"
    openrouter_api_key: str | None = None 
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"
    enable_retrieval_trace: bool = False

    model_config = {"env_prefix": "ISRA_"}

settings = Settings()
