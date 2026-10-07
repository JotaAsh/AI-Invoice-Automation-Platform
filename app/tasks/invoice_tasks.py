import asyncio
import logging
from functools import wraps

from app.core.celery_app import celery_app
from app.db.session import async_session_factory
from app.models.invoice import InvoiceStatus
from app.repositories.invoice_repository import InvoiceRepository
from app.services.ocr_service import OCRService
from app.services.validation_engine import ValidationEngine
from app.services.webhook_dispatcher import WebhookDispatcher

logger = logging.getLogger(__name__)


def async_to_sync(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@celery_app.task(bind=True, max_retries=3)
@async_to_sync
async def process_invoice_pipeline_task(self, invoice_id: int):
    """
    Main pipeline task that orchestrates:
    1. OCR / Data Extraction
    2. Rule Validation / Risk Scoring
    3. Dispatch to External Workflow Engine (Make / Zapier)
    """
    logger.info(f"Starting processing pipeline for invoice {invoice_id}")

    async with async_session_factory() as session:
        invoice_repo = InvoiceRepository(session)
        invoice = await invoice_repo.get(invoice_id)

        if not invoice:
            logger.error(f"Invoice {invoice_id} not found.")
            return

        try:
            # 1. Simulate OCR Extraction
            extracted_data = await OCRService.extract(invoice.deduplication_hash)

            # 2. Validation & Scoring
            validation_result = ValidationEngine.validate(extracted_data)

            # Update invoice based on results
            update_data = {
                "vendor_id": extracted_data.get("vendor_id"),
                "total_amount": extracted_data.get("total_amount"),
                "tax_amount": extracted_data.get("tax_amount"),
                "currency": extracted_data.get("currency", "USD"),
                "invoice_date": extracted_data.get("invoice_date"),
                "status": InvoiceStatus.VALIDATED
                if validation_result["is_valid"]
                else InvoiceStatus.READY_REVIEW,
            }

            await invoice_repo.update(invoice, update_data)
            await session.commit()

            # 3. Webhook Dispatch to Make / n8n
            webhook_payload = {
                "invoice_id": invoice_id,
                "status": update_data["status"].value,
                "extracted_data": extracted_data,
                "validation_result": validation_result,
            }

            await WebhookDispatcher.send(webhook_payload)

            logger.info(f"Successfully processed invoice {invoice_id}")

        except Exception as e:
            logger.error(f"Failed processing invoice {invoice_id}: {e!s}")
            await invoice_repo.update(invoice, {"status": InvoiceStatus.FAILED})
            await session.commit()
            raise self.retry(exc=e, countdown=10)
