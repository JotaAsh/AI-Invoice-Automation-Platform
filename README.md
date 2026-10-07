# AI Invoice Automation Platform

An open-source, async-first backend for automating the ingestion, OCR extraction, validation, and syncing of incoming invoices to external ERPs or workflows.

## Overview

This project provides a robust, asynchronous pipeline to process invoices at scale. It includes idempotency checks, a queued task system, and flexible webhooks for orchestration tools like Make, Zapier, or n8n.

**Note:** This is a streamlined open-source version focusing on the core architecture and pipeline pattern. Complex business validations, internal auth routines, and vendor-specific integrations have been removed or simplified for general-purpose usage.

## Features

- **FastAPI Backend:** Fully asynchronous, modern REST APIs.
- **Strict Idempotency:** SHA-256 hashing blocks identical files from redundant processing.
- **Celery & Redis:** Robust task queueing for expensive I/O operations (OCR, LLM data extraction).
- **Validation Engine:** Extensible rules for calculating mathematical inconsistencies and assigning a risk score.
- **Webhook Dispatcher:** Easily pushes validated payloads to your n8n or Make workflows for downstream processing or human-in-the-loop review.
- **PostgreSQL & Alembic:** Persists invoice state machines and audit logs; includes `asyncpg` async migrations.
- **Docker Ready:** Comes with a complete `docker-compose.yml` for zero-configuration spin-up.

## Architecture

1. **Ingestion (`POST /api/v1/invoices/upload`)**: Checks deduplication, stores initial DB record, and dispatches to Celery.
2. **Task Queue (Celery Worker)**: Picks up the job, simulates network I/O to perform data extraction.
3. **Validation Engine**: Examines output, looks for flags, scores risk, updates status (`VALIDATED`, `READY_REVIEW`, `FAILED`).
4. **Webhook Delivery**: Calls external workflow (e.g. `WEBHOOK_URL` in `.env`).

## Getting Started

1. **Clone the repository.**
2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration (like WEBHOOK_URL)
   ```
3. **Start services:**
   ```bash
   docker-compose up --build
   ```

FastAPI will be available at `http://localhost:8000`. You can visit `http://localhost:8000/docs` for the interactive API documentation.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
