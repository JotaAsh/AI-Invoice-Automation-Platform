from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Assuming models are structured under app/models/
from app.models.invoice import Vendor
from app.repositories.base import BaseRepository


class VendorRepository(BaseRepository[Vendor]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Vendor, db_session)

    async def get_by_tax_id(self, tax_id: str) -> Vendor | None:
        """
        Domain-specific query to find a vendor by their Tax Identification Number (e.g., RNC, NIT, CIF).
        Crucial for establishing relationships during the invoice extraction flow.
        """
        result = await self.db.execute(
            select(self.model).filter(self.model.tax_id == tax_id)
        )
        return result.scalars().first()
