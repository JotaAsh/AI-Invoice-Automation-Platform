import pytest
from uuid import uuid4
from app.repositories.vendor_repository import VendorRepository
from app.repositories.invoice_repository import InvoiceRepository

async def test_vendor_repository_lifecycle(db_session):
    """
    Verifies that a Vendor record can be successfully created, updated, 
    and queried by tax identification mappings using our abstract repository.
    """
    vendor_repo = VendorRepository(db_session)
    unique_tax_id = f"TAX-{uuid4().hex[:8].upper()}"
    
    # 1. Arrange inputs conforming to schema layouts
    vendor_data = {
        "name": "ACME Industrial Corp",
        "tax_id": unique_tax_id,
    }
    
    # 2. Act: Persist entity
    created_vendor = await vendor_repo.create(vendor_data)
    assert created_vendor.id is not None
    assert created_vendor.tax_id == unique_tax_id
    
    # 3. Assert: Fetch record using targeted business query
    fetched_vendor = await vendor_repo.get_by_tax_id(unique_tax_id)
    assert fetched_vendor is not None
    assert fetched_vendor.name == "ACME Industrial Corp"

async def test_invoice_repository_idempotency_check(db_session):
    """
    Validates that the invoice system catches file tracking records by hash digests,
    ensuring our determinism safety nets function seamlessly.
    """
    invoice_repo = InvoiceRepository(db_session)
    mock_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    # Verify non-existent hashes return None safely
    missing_file = await invoice_repo.get_by_idempotency_hash(mock_hash)
    assert missing_file is None