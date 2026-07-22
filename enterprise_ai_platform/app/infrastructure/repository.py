import time
import uuid
import json
from functools import lru_cache
from typing import Optional, Dict, Any
from app.core.schemas import JobCreateRequest, JobStatus
from app.infrastructure.aws.client import get_dynamodb_resource, get_sqs_resource, get_s3_client
from app.config import settings

class DynamoJobRepository:
    """Production-grade State Engine backed by AWS DynamoDB, SQS, and S3."""
    def __init__(self):
        # 1. Core State Store Setup
        self.db = get_dynamodb_resource()
        self.table = self.db.Table(settings.DYNAMODB_TABLE_NAME)
        
        # 2. Async Message Broker Setup
        self.sqs = get_sqs_resource()
        self.queue = self.sqs.get_queue_by_name(QueueName=settings.AWS_SQS_QUEUE_NAME)

        # 3. 🔥 S3 Client Setup
        self.s3 = get_s3_client()
        self.bucket_name = settings.AWS_S3_BUCKET_NAME

    def create(self, request: JobCreateRequest) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = time.time()
        
        job_record = {
            "job_id": job_id,
            "status": JobStatus.PENDING.value,
            "created_at": int(now),
            "updated_at": int(now),
            "payloads": request.payloads,
            "metadata": request.metadata or {},
            "error_message": ""
        }
        
        self.table.put_item(Item=job_record)
        
        message_body = {
            "job_id": job_id,
            "task_payload": request.payloads
        }
        
        self.queue.send_message(MessageBody=json.dumps(message_body))
        return job_record

    # 🔥 PHASE 2: Create job backed by S3 file storage
    def create_from_file(self, filename: str, file_content: bytes, content_type: str) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = time.time()
        
        # Define deterministic S3 Object Key
        s3_key = f"raw/{job_id}/{filename}"

        # 1. Upload raw binary to S3 Virtualization Grid
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type
        )

        # 2. Persist State in DynamoDB referencing S3 path
        job_record = {
            "job_id": job_id,
            "status": JobStatus.PENDING.value,
            "created_at": int(now),
            "updated_at": int(now),
            "payloads": [f"s3://{self.bucket_name}/{s3_key}"],
            "metadata": {
                "source": "file_upload",
                "filename": filename,
                "s3_bucket": self.bucket_name,
                "s3_key": s3_key
            },
            "error_message": ""
        }
        
        self.table.put_item(Item=job_record)

        # 3. Send lightweight S3 pointer event to SQS
        message_body = {
            "job_id": job_id,
            "s3_bucket": self.bucket_name,
            "s3_key": s3_key,
            "task_payload": [f"s3://{self.bucket_name}/{s3_key}"]
        }
        
        self.queue.send_message(MessageBody=json.dumps(message_body))
        return job_record

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        response = self.table.get_item(Key={"job_id": job_id})
        return response.get("Item")

@lru_cache(maxsize=1)
def get_job_repo() -> DynamoJobRepository:
    return DynamoJobRepository()