from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env up front so settings resolve regardless of import order.
load_dotenv()


class Settings(BaseSettings):
    llm_model: str = "anthropic/claude-haiku-4.5"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    model_config = {"env_prefix": "ISRA_"}


settings = Settings()
