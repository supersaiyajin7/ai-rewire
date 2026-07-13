import os
import boto3

# Pick up the container network address (http://localstack:4566) injected by docker-compose
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

def get_dynamodb_resource():
    """Returns a high-level DynamoDB Resource object pointing to our container mesh."""
    return boto3.resource(
        "dynamodb",
        region_name=AWS_REGION,
        endpoint_url=AWS_ENDPOINT_URL,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "mock_key"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "mock_secret")
    )