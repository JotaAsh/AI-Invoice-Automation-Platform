import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


class OCRService:
    @staticmethod
    async def extract(file_hash: str) -> dict[str, Any]:
        """
        Simulate OCR and LLM data extraction from a document.
        In a real scenario, this would call Tesseract, AWS Textract, or an LLM (Gemini/GPT-4V).
        """
        logger.info(f"Extracting data for file_hash: {file_hash}")

        # Simulate network/processing delay
        await asyncio.sleep(2)

        # Simulated extraction response
        return {
            "vendor_id": 1,  # Mock vendor ID matching DB
            "vendor_tax_id": "B12345678",
            "vendor_name": "Acme Corp Ltd",
            "invoice_number": f"INV-{file_hash[:6].upper()}",
            "total_amount": Decimal("1500.50"),
            "tax_amount": Decimal("250.00"),
            "currency": "USD",
            "invoice_date": datetime.now(UTC),
            "line_items": [
                {
                    "description": "Software License",
                    "quantity": 1,
                    "unit_price": 1000.00,
                    "total": 1000.00,
                },
                {
                    "description": "Consulting Services",
                    "quantity": 5,
                    "unit_price": 50.10,
                    "total": 250.50,
                },
            ],
        }
