import enum
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, JSON, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base # Assuming declarative base is configured here

class InvoiceStatus(enum.Enum):
    RECEIVED = "received"       # File uploaded, checking idempotency/malware
    PROCESSING = "processing"   # In Celery queue (OCR / LLM running)
    READY_REVIEW = "ready_review" # Extracted, failed some validation (human check needed)
    VALIDATED = "validated"     # Approved and ready for ERP sync
    SYNCED = "synced"           # Successfully pushed to external ERP via n8n/Make
    FAILED = "failed"           # Unrecoverable error (corrupt file, etc.)


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    tax_id = Column(String(50), unique=True, index=True, nullable=False) # CIF/NIF/RUT
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="vendor")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    # Business unique key (e.g., hash of Vendor TaxID + Invoice Number) to prevent duplicates
    deduplication_hash = Column(String(64), unique=True, index=True, nullable=True)
    
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True) # Nullable until OCR extracts it
    invoice_number = Column(String(100), nullable=True)
    
    # Financial data using precise Numeric type for currency
    total_amount = Column(Numeric(12, 2), nullable=True)
    tax_amount = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="USD")
    
    invoice_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    
    # State Machine & Orchestration
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.RECEIVED, nullable=False)
    external_workflow_id = Column(String(255), nullable=True) # n8n / Make execution ID
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vendor = relationship("Vendor", back_populates="invoices")
    files = relationship("InvoiceFile", back_populates="invoice", cascade="all, delete-orphan")
    audit_logs = relationship("InvoiceAuditLog", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceFile(Base):
    __tablename__ = "invoice_files"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Technical unique key to block immediate double-clicks on the same file
    idempotency_key = Column(String(64), unique=True, index=True, nullable=False)
    
    file_path = Column(String(512), nullable=False) # S3 / Local Storage destination
    file_type = Column(String(50)) # e.g., "application/pdf", "image/png"
    
    # AI / Parsing payloads
    ocr_raw_text = Column(JSON, nullable=True) # Full text dump from Tesseract/pdfplumber
    llm_raw_extraction = Column(JSON, nullable=True) # Raw JSON response from Gemini
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="files")


class InvoiceAuditLog(Base):
    __tablename__ = "invoice_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    action = Column(String(100), nullable=False) # e.g., "OCR_EXTRACTED", "STATUS_CHANGED", "ERP_SYNCED"
    description = Column(String(500), nullable=False)
    user_id = Column(String(100), nullable=True) # If triggered by a human reviewer in n8n
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="audit_logs")