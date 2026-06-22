# Import all models here so that Alembic can detect them dynamically
from app.db.base_class import Base
from app.models.invoice import Vendor, Invoice, InvoiceFile, InvoiceAuditLog

__all__ = ["Base", "Vendor", "Invoice", "InvoiceFile", "InvoiceAuditLog"]