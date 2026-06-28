from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    llm_model: str = "anthropic/claude-3-5-haiku-20241022"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    model_config = {"env_prefix": "ISRA_"}

settings = Settings()
