import hashlib
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.invoice import InvoiceStatus
from app.repositories.invoice_repository import InvoiceRepository
from app.schemas.invoice import InvoiceUploadResponse
from app.tasks.invoice_tasks import process_invoice_pipeline_task

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
    summary="Upload an invoice file to trigger automated processing pipeline",
)
async def upload_invoice(
    file: UploadFile = File(
        ..., description="PDF or image containing the vendor invoice"
    ),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Accepts multipart file uploads, checks for immediate network/file duplicates via SHA-256,
    persists a pending execution log, and dispatches processing asynchronously.
    """
    # 1. Enforce strict type validation
    allowed_content_types = ["application/pdf", "image/jpeg", "image/png", "image/tiff"]
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file.content_type}'. Supported formats: PDF, JPEG, PNG, TIFF.",
        )

    # 2. Read contents and evaluate idempotency hash
    contents = await file.read()
    file_hash = calculate_sha256(contents)

    invoice_repo = InvoiceRepository(db)

    # Check if this exact file asset has been uploaded and processed previously
    existing_invoice = await invoice_repo.get_by_idempotency_hash(file_hash)
    if existing_invoice:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This identical invoice file has already been uploaded and processed.",
        )

    # 3. Build a dictionary conforming to the Invoice model schema
    # Adjust these keys based on the exact properties required by your SQLAlchemy Invoice model.
    invoice_data = {
        "deduplication_hash": file_hash,
        "status": InvoiceStatus.PROCESSING,
        "invoice_number": "PENDING_EXTR_"
        + file_hash[:8].upper(),  # Temporary unique fallback
    }

    # Persist record utilizing the repository
    new_invoice_record = await invoice_repo.create(invoice_data)

    # 4. Asynchronous Task Delegation placeholder
    # Trigger Celery task
    process_invoice_pipeline_task.delay(new_invoice_record.id)

    # 5. Build tracking response
    return InvoiceUploadResponse(
        file_id=new_invoice_record.id,
        file_hash=file_hash,
        status=new_invoice_record.status.value,
        created_at=new_invoice_record.created_at,
        tracking_url=f"/api/v1/invoices/status/{new_invoice_record.id}",
    )


@router.get(
    "/status/{invoice_id}", summary="Check processing status of an uploaded invoice"
)
async def get_invoice_status(invoice_id: int, db: AsyncSession = Depends(get_db)):
    invoice_repo = InvoiceRepository(db)
    invoice = await invoice_repo.get(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found."
        )
    return {
        "invoice_id": invoice.id,
        "status": invoice.status.value,
        "total_amount": invoice.total_amount,
        "currency": invoice.currency,
        "created_at": invoice.created_at,
        "updated_at": invoice.updated_at,
    }
