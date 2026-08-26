from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "高校自动排课系统"
    app_version: str = "0.1.0"
    debug: bool = False

    # 数据库：默认 SQLite，生产环境用 DATABASE_URL 环境变量覆盖为 PostgreSQL
    database_url: str = "sqlite:///./schedule.db"

    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24小时

    # 排课默认配置
    default_schedule_time_limit: int = 120
    default_days_per_week: int = 5
    default_sections_per_day: int = 10

    # CORS 允许的来源（逗号分隔），* 表示全部允许
    cors_origins: str = "*"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
