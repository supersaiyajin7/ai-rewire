#!/usr/bin/env python3
"""
Enterprise AI Platform - Background Worker
Polls SQS queue, processes jobs, downloads S3 documents if present, and updates DynamoDB status.
"""
import sys
import os
import time

print("🚀 [WORKER STARTUP] Worker process container booted successfully!", flush=True)
print("⏳ [WORKER STARTUP] Waiting 5 seconds for AWS local mesh initialization...", flush=True)
time.sleep(5)

import json
from typing import Dict, Any

from app.config import settings
from app.infrastructure.aws.client import get_sqs_resource, get_dynamodb_resource, get_s3_client
from app.core.schemas import JobStatus

CONNECT_RETRY_SECONDS = 5


def get_env_config() -> Dict[str, str]:
    """Pull configuration from shared settings for consistent runtime behavior."""
    return {
        "queue_name": settings.AWS_SQS_QUEUE_NAME,
        "table_name": settings.DYNAMODB_TABLE_NAME,
        "bucket_name": settings.AWS_S3_BUCKET_NAME,
        "region": settings.AWS_REGION,
        "endpoint_url": settings.AWS_ENDPOINT_URL,
        "environment": settings.ENVIRONMENT,
    }


def init_clients(config: Dict[str, str]):
    """Initialize SQS, DynamoDB, and S3 clients with retry handling."""
    while True:
        try:
            print(f"📡 Connecting to SQS Queue: '{config['queue_name']}'...", flush=True)
            sqs = get_sqs_resource()
            queue = sqs.get_queue_by_name(QueueName=config["queue_name"])

            print(f"📡 Connecting to DynamoDB Table: '{config['table_name']}'...", flush=True)
            dynamodb = get_dynamodb_resource()
            table = dynamodb.Table(config["table_name"])

            print(f"📡 Connecting to S3 Client...", flush=True)
            s3 = get_s3_client()

            print("✅ Successfully connected to LocalStack infrastructure!", flush=True)
            return queue, table, s3
        except Exception as e:
            print(f"⏳ Waiting for AWS resources to exist in LocalStack... ({e})", flush=True)
            time.sleep(CONNECT_RETRY_SECONDS)


def process_job_payload(s3_client, s3_bucket: str, s3_key: str, payload: list) -> Dict[str, Any]:
    """
    S3 Stream Ingestion & Processing.
    Reads document from S3 if s3_bucket/s3_key exist, otherwise processes text payload.
    """
    file_info = {}

    if s3_bucket and s3_key:
        print(f"📥 Streaming object from S3 Grid: s3://{s3_bucket}/{s3_key}", flush=True)
        s3_object = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        content_bytes = s3_object['Body'].read()
        file_size = len(content_bytes)

        print(f"📄 Retrieved document: {s3_key} ({file_size} bytes)", flush=True)
        file_info = {
            "s3_path": f"s3://{s3_bucket}/{s3_key}",
            "file_size_bytes": file_size,
            "content_type": s3_object.get("ContentType", "unknown")
        }

    print(f"🔄 Processing workload...", flush=True)
    time.sleep(2)  # Simulate downstream processing

    return {
        "processed_count": len(payload) if payload else 1,
        "s3_metadata": file_info,
        "summary": "Phase 2 Object Ingestion & Storage complete"
    }


def update_job_status(table, job_id: str, status: JobStatus,
                       result: Dict[str, Any] = None,
                       error: str = None):
    """Update job status in DynamoDB with optional result or error."""
    update_expr = "SET #s = :s, updated_at = :t"
    expr_names = {"#s": "status"}
    expr_values = {
        ":s": status.value,
        ":t": int(time.time())
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


def poll_and_process(queue, table, s3_client, config: Dict[str, str]):
    """Main worker loop: poll SQS, stream from S3 if referenced, process, and update state."""
    print(f"🚀 Worker Active | Queue: {config['queue_name']} | Table: {config['table_name']}", flush=True)
    print("🔄 Polling SQS queue for incoming jobs...", flush=True)

    while True:
        try:
            messages = queue.receive_messages(
                MaxNumberOfMessages=10,
                WaitTimeSeconds=10,
                VisibilityTimeout=30
            )

            if not messages:
                continue

            print(f"📥 Received {len(messages)} message(s) from SQS", flush=True)

            for msg in messages:
                try:
                    body = json.loads(msg.body)
                    job_id = body.get("job_id")
                    s3_bucket = body.get("s3_bucket")
                    s3_key = body.get("s3_key")
                    task_payload = body.get("task_payload", [])

                    if not job_id:
                        print(f"⚠️ Message missing job_id, deleting", flush=True)
                        msg.delete()
                        continue

                    print(f"📋 Processing job_id: {job_id}", flush=True)

                    # 1. Update status to PROCESSING
                    update_job_status(table, job_id, JobStatus.PROCESSING)
                    print(f"🔄 Status updated -> PROCESSING", flush=True)

                    # 2. Process payload & download S3 object if present
                    try:
                        result = process_job_payload(s3_client, s3_bucket, s3_key, task_payload)

                        # 3. Update to COMPLETED
                        update_job_status(table, job_id, JobStatus.COMPLETED, result=result)
                        print(f"✅ Status updated -> COMPLETED", flush=True)

                    except Exception as e:
                        error_msg = f"{type(e).__name__}: {str(e)}"
                        update_job_status(table, job_id, JobStatus.FAILED, error=error_msg)
                        print(f"❌ Processing failed: {error_msg}", flush=True)

                    # 4. Delete message from queue
                    msg.delete()

                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON in message, deleting", flush=True)
                    msg.delete()

        except Exception as e:
            print(f"⚠️ Polling loop exception: {e}", flush=True)
            time.sleep(CONNECT_RETRY_SECONDS)


def main():
    config = get_env_config()
    queue, table, s3_client = init_clients(config)
    poll_and_process(queue, table, s3_client, config)


if __name__ == "__main__":
    main()