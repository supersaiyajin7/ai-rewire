#!/usr/bin/env python3
"""
Enterprise AI Platform - Background Worker
Polls SQS queue, processes jobs, and updates DynamoDB status.
"""
import json
import sys
import time
from typing import Dict, Any

from app.config import settings
from app.infrastructure.aws.client import get_sqs_resource, get_dynamodb_resource
from app.core.schemas import JobStatus

CONNECT_RETRY_SECONDS = 3


def get_env_config() -> Dict[str, str]:
    """Pull configuration from shared settings for consistent runtime behavior."""
    return {
        "queue_name": settings.AWS_SQS_QUEUE_NAME,
        "table_name": settings.DYNAMODB_TABLE_NAME,
        "region": settings.AWS_REGION,
        "endpoint_url": settings.AWS_ENDPOINT_URL,
        "environment": settings.ENVIRONMENT,
    }


def init_clients(config: Dict[str, str]):
    """Initialize SQS and DynamoDB clients."""
    # SQS
    sqs = get_sqs_resource()
    queue = sqs.get_queue_by_name(QueueName=config["queue_name"])

    # DynamoDB
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(config["table_name"])

    return queue, table


def process_job_payload(payload: list) -> Dict[str, Any]:
    """
    Placeholder for actual AI processing logic.
    In Phase 3, this will call Bedrock/LLM for extraction/classification.
    For Phase 1, we simulate processing and return a mock result.
    """
    print(f"  🔄 Processing {len(payload)} payload items...")

    # Simulate processing time
    time.sleep(1)

    # Mock result structure - replace with actual AI logic in Phase 3
    return {
        "processed_count": len(payload),
        "summary": "Mock processing complete",
        "items": [{"original": item, "processed": True} for item in payload]
    }


def update_job_status(table, job_id: str, status: JobStatus,
                      result: Dict[str, Any] = None,
                      error: str = None):
    """Update job status in DynamoDB with optional result or error."""
    import time as time_module

    update_expr = "SET #s = :s, updated_at = :t"
    expr_names = {"#s": "status"}
    expr_values = {
        ":s": status.value,
        ":t": int(time_module.time())
    }

    if result is not None:
        update_expr += ", #r = :r"
        expr_names["#r"] = "processing_result"
        expr_values[":r"] = json.dumps(result)

    if error is not None:
        update_expr += ", error_message = :e"
        expr_values[":e"] = error

    table.update_item(
        Key={"job_id": job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values
    )


def poll_and_process(queue, table, config: Dict[str, str]):
    """Main worker loop: poll SQS, process messages, update DynamoDB."""
    print(f"🔄 Worker started | Queue: {config['queue_name']} | Table: {config['table_name']}")
    print("   Polling for messages (long-poll 20s)...")

    while True:
        try:
            # Long-poll for messages (max 10, wait up to 20 seconds)
            messages = queue.receive_messages(
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
                VisibilityTimeout=30  # Message hidden for 30s while processing
            )

            if not messages:
                continue  # No messages, loop again

            print(f"📥 Received {len(messages)} message(s)")

            for msg in messages:
                try:
                    body = json.loads(msg.body)
                    job_id = body.get("job_id")
                    task_payload = body.get("task_payload", [])

                    if not job_id:
                        print(f"  ⚠️  Message missing job_id, deleting: {msg.body[:100]}")
                        msg.delete()
                        continue

                    print(f"  📋 Processing job: {job_id}")

                    # 1. Update status to PROCESSING
                    update_job_status(table, job_id, JobStatus.PROCESSING)
                    print(f"  🔄 Status -> PROCESSING")

                    # 2. Process the payload (Phase 3: replace with real AI logic)
                    try:
                        result = process_job_payload(task_payload)

                        # 3. Update to COMPLETED with result
                        update_job_status(table, job_id, JobStatus.COMPLETED, result=result)
                        print(f"  ✅ Status -> COMPLETED")

                    except Exception as e:
                        # 4. On failure, update to FAILED with error
                        error_msg = f"{type(e).__name__}: {str(e)}"
                        update_job_status(table, job_id, JobStatus.FAILED, error=error_msg)
                        print(f"  ❌ Status -> FAILED: {error_msg}")

                    # 5. Delete message from queue (success or failure - we've recorded state)
                    msg.delete()

                except json.JSONDecodeError:
                    print(f"  ⚠️  Invalid JSON in message, deleting: {msg.body[:100]}")
                    msg.delete()
                except Exception as e:
                    print(f"  ❌ Error processing message: {e}")
                    # Don't delete - let it become visible again after VisibilityTimeout
                    # Or implement dead-letter logic in Phase 4

        except KeyboardInterrupt:
            print("\n🛑 Worker shutting down...")
            break
        except Exception as e:
            print(f"  ❌ Polling error: {e}")
            time.sleep(5)  # Back off on connection errors


def main():
    """Entry point."""
    print("=" * 60)
    print("  ENTERPRISE AI PLATFORM - BACKGROUND WORKER")
    print("=" * 60)

    config = get_env_config()

    # Validate required config
    if not config["queue_name"] or not config["table_name"]:
        print("❌ Missing required environment variables:")
        print("   AWS_SQS_QUEUE_NAME, DYNAMODB_TABLE_NAME")
        sys.exit(1)

    while True:
        try:
            queue, table = init_clients(config)
            break
        except Exception as e:
            print(f"⏳ Worker waiting for AWS endpoints: {e}")
            time.sleep(CONNECT_RETRY_SECONDS)

    poll_and_process(queue, table, config)


if __name__ == "__main__":
    main()