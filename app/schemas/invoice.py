from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InvoiceUploadResponse(BaseModel):
    """
    Response schema returned immediately after a successful file submission.
    Adheres to RESTful asynchronous processing design (202 Accepted).
    """

    file_id: int = Field(
        ..., description="Unique identifier for the uploaded invoice file record"
    )
    file_hash: str = Field(
        ..., description="SHA-256 fingerprint used for strict idempotency verification"
    )
    status: str = Field(
        ...,
        description="Current status of the background parsing pipeline (e.g., 'processing')",
    )
    created_at: datetime = Field(
        ..., description="Timestamp of when the upload was registered"
    )
    tracking_url: str = Field(
        ..., description="API endpoint to poll for extraction status and results"
    )

    model_config = ConfigDict(from_attributes=True)
