from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
# Assuming models are structured under app/models/
from app.models.vendor import Vendor 

class VendorRepository(BaseRepository[Vendor]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Vendor, db_session)

    async def get_by_tax_id(self, tax_id: str) -> Optional[Vendor]:
        """
        Domain-specific query to find a vendor by their Tax Identification Number (e.g., RNC, NIT, CIF).
        Crucial for establishing relationships during the invoice extraction flow.
        """
        result = await self.db.execute(
            select(self.model).filter(self.model.tax_id == tax_id)
        )
        return result.scalars().first()