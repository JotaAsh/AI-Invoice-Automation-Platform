from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.invoice import Invoice, InvoiceFile

class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Invoice, db_session)

    async def get_by_idempotency_hash(self, file_hash: str) -> Optional[InvoiceFile]:
        """
        Strict determinism rule: check if an invoice file has already been uploaded 
        and hashed to avoid duplicate ingestion processing pipelines.
        """
        # Relies on an index over idempotency_key field for high performance
        result = await self.db.execute(
            select(InvoiceFile).filter(InvoiceFile.idempotency_key == file_hash)
        )
        return result.scalars().first()

    async def get_duplicates(self, vendor_id: str, invoice_number: str) -> List[Invoice]:
        """
        Business validation logic: checks if the exact invoice number already exists 
        for the specified vendor, alerting potential clerical errors.
        """
        result = await self.db.execute(
            select(self.model).filter(
                self.model.vendor_id == vendor_id,
                self.model.invoice_number == invoice_number
            )
        )
        return list(result.scalars().all())