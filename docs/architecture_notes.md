# Architecture Notes & Pipeline Design

This document details the original design goals and logical pipeline flow for the AI Invoice Automation Platform.

## 1. Document Compliance Workflow Engine

**Goal:** Automate the reception, validation, and classification of documents for KYC/AML or standard compliance processes.

**Pipeline Flow:**
- User uploads documents (PDFs, IDs, Financial Statements).
- **FastAPI Gateway** receives the multi-part payload.
- **Worker Node (Celery)** extracts raw text (OCR).
- **Validation Engine** dynamically evaluates extracted data against compliance rules to detect anomalies.
- **Webhook Dispatcher** alerts external ERPs or workflows (Make / Zapier / Slack / Email).
- Dashboard or mobile app polls API for processing status.

**Tech Stack:**
- **FastAPI** → Core REST API
- **Docker** → Containerized microservices
- **Celery + Redis** → Asynchronous job processing & message brokering
- **PostgreSQL (Asyncpg)** → Relational persistence
- **Make/n8n/Zapier** → Alerts and human-in-the-loop approvals

**Key Differentiators:**
- Document risk scoring
- Dynamic validation rules
- External webhook extensibility

---

## 2. Intelligent Accounts Payable Pipeline

**Goal:** Convert incoming AP documents into structured JSON objects and trigger automated approval chains.

**Pipeline Flow:**
Email Inbox → Webhook → FastAPI → OCR + LLM Parsing → Extracted (Vendor/Amount/Taxes) → Validation Engine → Workflow (Make/n8n) → ERP Sync

**Complexity Solved:**
- Deduplication (Strict Idempotency via SHA-256)
- High-value alerts
- Math inconsistency detection

---

## MVP Components (Implemented)

- **Upload API** (Idempotent endpoint)
- **OCR Service (Mock/Placeholder)**
- **Validation & Risk Scoring Engine**
- **Webhook Dispatcher (HTTPX)**
- **Dockerized Deployment** (Postgres + Redis + API + Worker)
