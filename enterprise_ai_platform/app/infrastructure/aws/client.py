import os
import boto3

# 1. Pull settings from the environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# 2. Extract endpoints dynamically
# If the variable is blank or missing (like in real AWS Dev/Prod), it resolves to None
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL") or None

def get_dynamodb_resource():
    """Returns a high-level DynamoDB Resource object pointing dynamically to the cloud or local container mesh."""
    
    # In local development, pass mock keys so boto3 doesn't look for host config files.
    # In cloud environments, let it fall back to None so IAM execution roles handle authentication.
    if ENVIRONMENT == "local":
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID", "mock_key")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "mock_secret")
    else:
        aws_access_key = None
        aws_secret_key = None

    return boto3.resource(
        "dynamodb",
        region_name=AWS_REGION,
        endpoint_url=AWS_ENDPOINT_URL,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )