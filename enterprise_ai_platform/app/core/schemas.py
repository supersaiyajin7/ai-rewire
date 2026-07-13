from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobCreateRequest(BaseModel):
    payloads: List[str] = Field(..., description="List of items or documents to process asynchronously.")
    metadata: Optional[Dict[str, Any]] = None

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: float
    updated_at: float
    error_message: Optional[str] = None