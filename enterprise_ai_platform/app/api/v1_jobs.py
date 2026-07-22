from fastapi import APIRouter, HTTPException, status, UploadFile, File
from app.core.schemas import JobCreateRequest, JobResponse
from app.infrastructure.repository import get_job_repo

router = APIRouter(prefix="/v1/jobs", tags=["Job Lifecycle Engine"])

@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
def trigger_batch_job(request: JobCreateRequest):
    """Ingest a standard text workload and return an HTTP 202 tracking contract immediately."""
    if not request.payloads:
        raise HTTPException(status_code=400, detail="Payload collection cannot be empty.")

    return get_job_repo().create(request)

# 🔥 PHASE 2: Unstructured File Ingestion Endpoint
@router.post("/upload", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
async def trigger_file_job(file: UploadFile = File(...)):
    """Ingest a raw binary file (PDF, TXT, Image), store in S3, and start processing pipeline."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a valid filename.")

    file_bytes = await file.read()
    return get_job_repo().create_from_file(
        filename=file.filename,
        file_content=file_bytes,
        content_type=file.content_type or "application/octet-stream"
    )

@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str):
    """Poll the status engine for an existing job tracking sequence."""
    job = get_job_repo().get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job sequence {job_id} not found.")
    return job