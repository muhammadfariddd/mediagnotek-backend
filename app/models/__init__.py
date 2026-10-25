# Export all models for easy access: from app.models import ...
from app.models.facility import Facility, User
from app.models.supplier import Supplier, PurchaseInvoice, PurchaseInvoiceItem
from app.models.drug import (
    Disease,
    Symptom,
    Drug,
    DrugBatch,
    DrugInteraction,
    StockPrediction,
    disease_drug,
    disease_symptom,
)
from app.models.patient import Patient
from app.models.transaction import Transaction, TransactionItem
from app.models.audit import StockMutation, CashFlow
from app.models.ai import AIConsultationSession, AIConsultationMessage

__all__ = [
    # Facility & Users
    "Facility",
    "User",
    # Suppliers & Procurement
    "Supplier",
    "PurchaseInvoice",
    "PurchaseInvoiceItem",
    # Drugs & Knowledge Base
    "Disease",
    "Symptom",
    "Drug",
    "DrugBatch",
    "DrugInteraction",
    "StockPrediction",
    "disease_drug",
    "disease_symptom",
    # Patients & Records
    "Patient",
    # POS & Financial Snapshotting
    "Transaction",
    "TransactionItem",
    # Audit & Cash Flow
    "StockMutation",
    "CashFlow",
    # AI Clinical Chat
    "AIConsultationSession",
    "AIConsultationMessage",
]
