import time
import uuid
from typing import Optional, Dict, Any
from app.core.schemas import JobCreateRequest, JobStatus
from app.infrastructure.aws.client import get_dynamodb_resource

class DynamoJobRepository:
    """Production-grade State Engine backed by AWS DynamoDB (LocalStack)."""
    def __init__(self):
        self.db = get_dynamodb_resource()
        self.table = self.db.Table("platform_jobs")

    def create(self, request: JobCreateRequest) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = time.time()
        
        job_record = {
            "job_id": job_id,
            "status": JobStatus.PENDING.value, # DynamoDB stores primitives
            "created_at": int(now),
            "updated_at": int(now),
            "payloads": request.payloads,
            "metadata": request.metadata or {},
            "error_message": ""
        }
        
        # Atomic PUT item into our LocalStack DynamoDB
        self.table.put_item(Item=job_record)
        return job_record

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        response = self.table.get_item(Key={"job_id": job_id})
        item = response.get("Item")
        
        if not item:
            return None
            
        # Ensure primitive string transforms back cleanly to schema types
        return item

# Swap out the global variable instance to use DynamoDB seamlessly
job_repo = DynamoJobRepository()