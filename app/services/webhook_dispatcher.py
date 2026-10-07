import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    @staticmethod
    async def send(payload: dict[str, Any]) -> None:
        """
        Dispatches the processed invoice data to an external automation tool like Make, n8n or Zapier.
        """
        webhook_url = settings.WEBHOOK_URL
        if not webhook_url or webhook_url == "https://hook.us1.make.com/xxxxxxxxx":
            logger.warning(
                "No valid WEBHOOK_URL configured. Skipping webhook dispatch."
            )
            return

        logger.info(f"Dispatching webhook to {webhook_url}")

        # We use a custom encoder or we assume the payload is already JSON serializable.
        # Ensure Decimal and datetime are converted to strings/floats.
        clean_payload = WebhookDispatcher._serialize_payload(payload)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    webhook_url, json=clean_payload, timeout=10.0
                )
                response.raise_for_status()
                logger.info("Webhook dispatched successfully")
            except httpx.HTTPError as e:
                logger.error(f"Failed to dispatch webhook: {e}")
                # We could raise an exception here to allow Celery to retry,
                # but depending on business logic, we might just log it or save to a dead-letter queue.
                raise

    @staticmethod
    def _serialize_payload(obj: Any) -> Any:
        from datetime import date, datetime
        from decimal import Decimal

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, dict):
            return {k: WebhookDispatcher._serialize_payload(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [WebhookDispatcher._serialize_payload(i) for i in obj]
        return obj
