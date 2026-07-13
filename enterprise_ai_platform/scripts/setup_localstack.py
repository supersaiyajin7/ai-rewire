"""DevOps / Infra bootstrapper scripts for LocalStack services"""
import sys
import os

# Appends the root directory to path so script can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.aws.client import get_dynamodb_client

def initialize_infrastructure():
    client = get_dynamodb_client()
    
    print("Checking/Creating DynamoDB tables in LocalStack...")
    try:
        # Check if table already exists
        existing_tables = client.list_tables()["TableNames"]
        if "platform_jobs" in existing_tables:
            print("Table 'platform_jobs' already exists. Skipping initialization.")
            return

        client.create_table(
            TableName="platform_jobs",
            KeySchema=[
                {"AttributeName": "job_id", "KeyType": "HASH"}  # Partition Key
            ],
            AttributeDefinitions=[
                {"AttributeName": "job_id", "AttributeType": "S"}
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )
        print("Successfully created 'platform_jobs' table in LocalStack!")
    except Exception as e:
        print(f"Failed to talk to LocalStack. Is docker container running? Error: {e}")

if __name__ == "__main__":
    initialize_infrastructure()
