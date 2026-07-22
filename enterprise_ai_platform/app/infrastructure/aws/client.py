import boto3
from app.config import settings

def _get_boto3_kwargs():
    """Build boto3 kwargs from shared settings for consistent API/worker behavior."""
    kwargs = {
        "region_name": settings.AWS_REGION,
        "endpoint_url": settings.AWS_ENDPOINT_URL,
    }
    if settings.ENVIRONMENT == "local":
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID or "mock_key"
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY or "mock_secret"
    return kwargs

def get_dynamodb_resource():
    """Returns a high-level DynamoDB Resource object pointing dynamically to the stack mesh."""
    return boto3.resource(
        "dynamodb",
        **_get_boto3_kwargs()
    )

# 🔥 NEW: High-level client for our Phase 1 SQS Ingestion Layer
def get_sqs_resource():
    """Returns a high-level SQS Resource object pointing dynamically to the stack mesh."""
    return boto3.resource(
        "sqs",
        **_get_boto3_kwargs()
    )

def get_s3_resource():
    """Returns a boto3 S3 Resource configured for LocalStack or AWS."""
    return boto3.resource(
        "s3",
        region_name=settings.AWS_REGION,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

def get_s3_client():
    """Returns a boto3 S3 Client configured for LocalStack or AWS."""
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

