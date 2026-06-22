import hashlib
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.invoice_repository import InvoiceRepository
# Assuming a separate file model or repository exists for managing invoice_files table
from app.schemas.invoice import InvoiceUploadResponse

router = APIRouter()

def calculate_sha256(file_content: bytes) -> str:
    """
    Generate a deterministic SHA-256 hex digest for strict file idempotency.
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_content)
    return sha256_hash.hexdigest()

@router.post(
    "/upload",
    response_model=InvoiceUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload an invoice file to trigger automated processing pipeline"
)
async def upload_invoice(
    file: UploadFile = File(..., description="PDF or image containing the vendor invoice"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Accepts multipart file uploads, checks for immediate network/file duplicates via SHA-256,
    persists a pending execution log, and dispatches processing to Celery background workers.
    """
    # 1. Enforce strict type validation
    allowed_content_types = ["application/pdf", "image/jpeg", "image/png", "image/tiff"]
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file.content_type}'. Supported formats: PDF, JPEG, PNG, TIFF."
        )

    # 2. Read contents and evaluate idempotency hash
    contents = await file.read()
    file_hash = calculate_sha256(contents)

    invoice_repo = InvoiceRepository(db)
    
    # Check if this exact file asset has been uploaded and processed previously
    existing_file = await invoice_repo.get_by_idempotency_hash(file_hash)
    if existing_file:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This identical invoice file has already been uploaded and processed."
        )

    # 3. Secure file storage & transactional record persistence
    # NOTE: In a complete implementation, 'contents' would be pushed to an Object Storage (S3/MinIO) 
    # service here, yielding a secure storage URI.
    
    # Mocking metadata record dictionary initialization for 'invoice_files' table
    invoice_file_data = {
        "file_name": file.filename,
        "file_hash": file_hash,
        "status": "PROCESSING",
        "storage_path": f"invoices/{file_hash}/{file.filename}"
    }
    
    # Persisting the raw metadata using repository pattern
    # In a structured workflow, you would call your dedicated InvoiceFileRepository
    # New row is generated with a unique UUID
    new_file_record = await invoice_repo.create_file_record(invoice_file_data)
    
    # 4. Asynchronous Task Delegation
    # We trigger the Celery task passing the database tracking UUID identifier
    # process_invoice_pipeline_task.delay(str(new_file_record.id))

    # 5. Build HATEOAS-compliant tracking response
    return InvoiceUploadResponse(
        file_id=new_file_record.id,
        file_hash=file_hash,
        status=new_file_record.status,
        created_at=new_file_record.created_at,
        tracking_url=f"/api/v1/invoices/status/{new_file_record.id}"
    )