import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


class ValidationEngine:
    @staticmethod
    def validate(extracted_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validates extracted invoice data and calculates risk scores.
        Checks for math consistencies, required fields, and threshold rules.
        """
        logger.info("Running validation and risk scoring rules...")

        flags = []
        is_valid = True
        risk_score = 0

        # 1. Missing Critical Fields
        required_fields = ["total_amount", "vendor_name", "invoice_number"]
        for field in required_fields:
            if not extracted_data.get(field):
                flags.append(f"Missing required field: {field}")
                is_valid = False
                risk_score += 40

        # 2. Math consistency: Does total equal line items + tax? (Simplified)
        total_amount = extracted_data.get("total_amount", Decimal("0.0"))
        line_items = extracted_data.get("line_items", [])

        calculated_subtotal = Decimal(
            str(sum(item.get("total", 0) for item in line_items))
        )
        tax = extracted_data.get("tax_amount", Decimal("0.0"))

        if line_items and (calculated_subtotal + tax != total_amount):
            flags.append("Math inconsistency: Line items + Tax != Total")
            is_valid = False
            risk_score += 30

        # 3. High Value Flag (Requires human review over $10k)
        if total_amount > Decimal("10000.0"):
            flags.append("High value invoice, manual approval required")
            is_valid = False
            risk_score += 20

        return {
            "is_valid": is_valid,
            "risk_score": min(risk_score, 100),
            "flags": flags,
        }
