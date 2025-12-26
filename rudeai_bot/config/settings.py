import os
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")

    # Database
    database_url: str = Field(default="sqlite:///rudeai_bot.db", env="DATABASE_URL")

    # OpenAI Configuration
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=40, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")

    # Webhook Configuration
    webhook_url: str = Field(..., env="WEBHOOK_URL")
    webhook_secret: str = Field(..., env="WEBHOOK_SECRET")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_retention: str = Field(default="30 days", env="LOG_RETENTION")

    # Security & Rate Limiting
    rate_limit_per_minute: int = Field(default=10, env="RATE_LIMIT_PER_MINUTE")
    max_message_length: int = Field(default=1000, env="MAX_MESSAGE_LENGTH")

    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_retention_days: int = Field(default=7, env="METRICS_RETENTION_DAYS")

    # Task Scheduler
    scheduler_test_mode: bool = Field(default=False, env="SCHEDULER_TEST_MODE")

    # PostgreSQL (for production)
    postgres_password: Optional[str] = Field(default=None, env="POSTGRES_PASSWORD")

    # Railway configuration
    railway_environment: Optional[str] = Field(default=None, env="RAILWAY_ENVIRONMENT")
    railway_deployment_id: Optional[str] = Field(default=None, env="RAILWAY_DEPLOYMENT_ID")
    railway_project_id: Optional[str] = Field(default=None, env="RAILWAY_PROJECT_ID")

    # System Prompt (keeping the same for consistency)
    system_prompt: str = Field(
        default=(
            "You are RUDE.AI, a brutal productivity drill sergeant.\n\n"
            "Rules:\n"
            "- One sentence only, ≤15 words.\n"
            "- Start with an action command.\n"
            "- Follow with a sharp, mocking sting.\n"
            "- Tone: cold, sarcastic, impatient.\n"
            "- Never empathetic, never soft, never explanatory.\n"
            "- No identity-based insults, no slurs, no self-harm.\n\n"
            "Examples:\n"
            'User: "I need to study for my exam."\n'
            'Assistant: "Open the book now. Your genius plan of panic is laughable."\n\n'
            'User: "Still avoiding laundry."\n'
            'Assistant: "Turn on the washer. Your avoidance smells worse than the clothes."\n\n'
            'User: "Scrolling TikTok again."\n'
            'Assistant: "Lock the phone. Even your thumbs are tired of your excuses."\n\n'
            'User: "Too tired to send the email."\n'
            'Assistant: "Write the draft. Fatigue is just your favorite costume."'
        ),
        env="SYSTEM_PROMPT"
    )

    @validator('environment')
    def validate_environment(cls, v):
        allowed_envs = ['development', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'Environment must be one of: {allowed_envs}')
        return v

    @validator('webhook_secret')
    def validate_webhook_secret(cls, v):
        if len(v) < 16:
            raise ValueError('Webhook secret must be at least 16 characters long')
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()