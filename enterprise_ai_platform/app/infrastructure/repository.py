import time
import uuid
import json
from functools import lru_cache
from typing import Optional, Dict, Any
from app.core.schemas import JobCreateRequest, JobStatus
from app.infrastructure.aws.client import get_dynamodb_resource, get_sqs_resource
from app.config import settings

class DynamoJobRepository:
    """Production-grade State Engine backed by AWS DynamoDB and SQS (LocalStack)."""
    def __init__(self):
        # 1. Core State Store Setup
        self.db = get_dynamodb_resource()
        self.table = self.db.Table(settings.DYNAMODB_TABLE_NAME)
        
        # 2. Async Message Broker Setup
        self.sqs = get_sqs_resource()
        self.queue = self.sqs.get_queue_by_name(QueueName=settings.AWS_SQS_QUEUE_NAME)

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
        
        # Atomic PUT item into our LocalStack DynamoDB
        self.table.put_item(Item=job_record)
        
        # Dispatch an asynchronous event message to SQS for downstream processing
        message_body = {
            "job_id": job_id,
            "task_payload": request.payloads
        }
        
        self.queue.send_message(
            MessageBody=json.dumps(message_body)
        )
        
        return job_record

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        response = self.table.get_item(Key={"job_id": job_id})
        item = response.get("Item")
        
        if not item:
            return None
            
        return item

@lru_cache(maxsize=1)
def get_job_repo() -> DynamoJobRepository:
    return DynamoJobRepository()