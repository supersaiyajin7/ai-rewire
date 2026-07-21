from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    AWS_REGION: str = "us-east-1"

    # By using Optional[str] = None, if the variable is blank in dev/prod,
    # it safely falls back to None so Boto3 connects to real AWS.
    AWS_ENDPOINT_URL: Optional[str] = None

    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    DYNAMODB_TABLE_NAME: str = "platform_jobs"
    AWS_SQS_QUEUE_NAME: str = "platform-job-queue"

    # Automatically tells Pydantic to read from the .env file if it exists
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Instantiated once as a singleton to share across the application
settings = Settings()