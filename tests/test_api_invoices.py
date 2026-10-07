import pytest
from io import BytesIO
from fastapi import status
from httpx import AsyncClient
from app.main import app
from app.db.session import get_db

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

async def test_upload_invoice_endpoint_success(db_session):
    """
    Verifies that uploading a valid PDF returns 202 Accepted and sets status to PROCESSING.
    """
    # Override FastAPI dependency injection to use the isolated test database session
    app.dependency_overrides[get_db] = lambda: db_session

    # Prepare a mock PDF structure in memory
    mock_pdf_content = b"%PDF-1.4 Mock Invoice Data for Testing Purposes"
    files = {
        "file": ("invoice_2026.pdf", BytesIO(mock_pdf_content), "application/pdf")
    }

    # Execute request against the application using the async HTTP client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/invoices/upload", files=files)

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["status"] == "processing"
    assert "file_id" in data
    assert "file_hash" in data

    # Clean up overrides
    app.dependency_overrides.clear()


async def test_upload_invoice_endpoint_duplicate_conflict(db_session):
    """
    Verifies that uploading the exact same file twice breaks on the idempotency check
    and returns a 409 Conflict exception.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    mock_pdf_content = b"%PDF-1.4 Identical Duplicate Content Asset"
    files = {
        "file": ("invoice_duplicate.pdf", BytesIO(mock_pdf_content), "application/pdf")
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First upload: Should succeed
        first_resp = await ac.post("/api/v1/invoices/upload", files=files)
        assert first_resp.status_code == status.HTTP_202_ACCEPTED

        # Second upload with identical payload: Must trigger 409 Conflict
        # Recreate files dict since BytesIO is exhausted after first read
        files_dup = {
            "file": ("invoice_duplicate.pdf", BytesIO(mock_pdf_content), "application/pdf")
        }
        second_resp = await ac.post("/api/v1/invoices/upload", files=files_dup)
        assert second_resp.status_code == status.HTTP_409_CONFLICT
        assert "already been uploaded" in second_resp.json()["detail"]

    app.dependency_overrides.clear()