"""AI Panel Studio — 配置管理（环境变量/Settings）"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DeepSeek
    deepseek_api_key: str = "sk-placeholder"
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

    model_config = {"env_file": ".env"}


settings = Settings()
