"""应用配置 — 严格遵循 BACKEND_STRUCTURE.md §6"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DeepSeek
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/ai_panel_studio.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Discussion
    default_expert_count: int = 4
    min_expert_count: int = 2
    max_expert_count: int = 8
    default_max_rounds: int | None = None
    auto_end_threshold: int = 3
    llm_max_retries: int = 2

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
