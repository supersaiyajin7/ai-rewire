from fastapi import APIRouter, HTTPException, status
from app.core.schemas import JobCreateRequest, JobResponse
from app.infrastructure.repository import job_repo

router = APIRouter(prefix="/v1/jobs", tags=["Job Lifecycle Engine"])

@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
def trigger_batch_job(request: JobCreateRequest):
    """Ingest a workload and return an HTTP 202 tracking contract immediately."""
    if not request.payloads:
        raise HTTPException(status_code=400, detail="Payload collection cannot be empty.")

    return job_repo.create(request)

@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str):
    """Poll the status engine for an existing job tracking sequence."""
    job = job_repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job sequence {job_id} not found.")
    return job