# backend/models.py - Enhanced with Dashboard Data Models

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

Base = declarative_base()

# Enum definitions for consistent data categorization
class UserRole(str, Enum):
    admin = "admin"
    staff = "staff"
    client = "client"

class JobStatus(str, Enum):
    active = "active"
    near_completion = "near_completion"
    completed = "completed"
    on_hold = "on_hold"

class ExpenseCategory(str, Enum):
    material = "material"
    labour = "labour"
    plant_machinery = "plant_machinery"
    overheads = "overheads"
    subcontractor = "subcontractor"

class VariationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

# Database Models - These represent the actual tables in your database
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(SQLEnum(UserRole))
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Job(Base):
    """
    Core job/project entity - think of this as the master record for each construction project
    This table holds all the fundamental information about each job that NDA undertakes
    """
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_code = Column(String, unique=True, index=True)  # e.g., "NDA-001"
    job_name = Column(String)  # e.g., "HV Cable Installation - Manchester"
    client = Column(String)  # e.g., "AIS Utilities", "SGN"
    contract_value = Column(Float)  # Original contract value
    amended_value = Column(Float)  # Contract value including approved variations
    estimated_final_cost = Column(Float)  # Projected total cost at completion
    status = Column(SQLEnum(JobStatus))
    progress_percentage = Column(Float, default=0.0)
    start_date = Column(DateTime)
    expected_completion_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - these create connections between different data tables
    expenses = relationship("Expense", back_populates="job")
    invoices = relationship("Invoice", back_populates="job")
    variations = relationship("Variation", back_populates="job")
    budgets = relationship("Budget", back_populates="job")

class Expense(Base):
    """
    Individual expense entries extracted from P&L reports
    Each row represents a specific cost item associated with a job
    """
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    category = Column(SQLEnum(ExpenseCategory))
    description = Column(String)
    amount = Column(Float)
    expense_date = Column(DateTime)
    reference = Column(String)  # Reference from P&L report
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job", back_populates="expenses")

class Invoice(Base):
    """
    Invoice tracking - both issued and payment status
    This helps track cash flow and outstanding receivables
    """
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    invoice_number = Column(String)
    amount = Column(Float)
    invoice_date = Column(DateTime)
    due_date = Column(DateTime)
    is_paid = Column(Boolean, default=False)
    paid_date = Column(DateTime)
    payment_reference = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job", back_populates="invoices")

class Variation(Base):
    """
    Contract variations - additional work orders that change the original scope
    These require client approval and affect the final contract value
    """
    __tablename__ = "variations"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    variation_number = Column(String)  # e.g., "VAR-001", "VAR-002"
    description = Column(Text)
    amount = Column(Float)
    status = Column(SQLEnum(VariationStatus))
    submitted_date = Column(DateTime)
    approved_date = Column(DateTime)
    approved_by = Column(String)  # Client representative who approved
    created_by = Column(String)  # NDA staff who created the variation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job", back_populates="variations")

class Budget(Base):
    """
    Budget allocations for different expense categories per job
    This enables budget vs actual comparisons and alerts
    """
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    category = Column(SQLEnum(ExpenseCategory))
    budgeted_amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    job = relationship("Job", back_populates="budgets")

class Alert(Base):
    """
    System alerts for budget overruns, overdue invoices, etc.
    This creates a notification system for important events
    """
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    alert_type = Column(String)  # e.g., "budget_overrun", "overdue_invoice"
    message = Column(Text)
    severity = Column(String)  # "low", "medium", "high"
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String)

# Pydantic Models - These define the data structure for API requests/responses
class JobBase(BaseModel):
    job_code: str
    job_name: str
    client: str
    contract_value: float
    amended_value: float
    estimated_final_cost: float
    status: JobStatus
    progress_percentage: float = 0.0
    start_date: Optional[datetime] = None
    expected_completion_date: Optional[datetime] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    job_name: Optional[str] = None
    client: Optional[str] = None
    contract_value: Optional[float] = None
    amended_value: Optional[float] = None
    estimated_final_cost: Optional[float] = None
    status: Optional[JobStatus] = None
    progress_percentage: Optional[float] = None
    expected_completion_date: Optional[datetime] = None

class JobResponse(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields that will be computed from related data
    total_costs: float = 0.0
    total_invoiced: float = 0.0
    pending_invoices: float = 0.0
    unpaid_invoices: float = 0.0
    projected_margin: float = 0.0
    
    class Config:
        from_attributes = True

class ExpenseBase(BaseModel):
    category: ExpenseCategory
    description: str
    amount: float
    expense_date: datetime
    reference: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    job_id: int

class ExpenseResponse(ExpenseBase):
    id: int
    job_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    invoice_number: str
    amount: float
    invoice_date: datetime
    due_date: datetime
    is_paid: bool = False
    paid_date: Optional[datetime] = None
    payment_reference: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    job_id: int

class InvoiceResponse(InvoiceBase):
    id: int
    job_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class VariationBase(BaseModel):
    variation_number: str
    description: str
    amount: float
    status: VariationStatus = VariationStatus.pending
    submitted_date: datetime
    created_by: str

class VariationCreate(VariationBase):
    job_id: int

class VariationUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[VariationStatus] = None
    approved_by: Optional[str] = None

class VariationResponse(VariationBase):
    id: int
    job_id: int
    approved_date: Optional[datetime] = None
    approved_by: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class BudgetBase(BaseModel):
    category: ExpenseCategory
    budgeted_amount: float

class BudgetCreate(BudgetBase):
    job_id: int

class BudgetResponse(BudgetBase):
    id: int
    job_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DashboardMetrics(BaseModel):
    """
    Aggregated metrics for dashboard display
    This model structures the key financial indicators that John needs to see
    """
    total_contract_value: float
    total_invoiced: float
    total_costs: float
    projected_margin: float
    pending_invoices: float
    unpaid_invoices: float
    active_jobs_count: int
    completed_jobs_count: int
    
class JobDetailMetrics(BaseModel):
    """
    Detailed metrics for a specific job
    This provides comprehensive financial overview for individual projects
    """
    job_code: str
    job_name: str
    client: str
    contract_value: float
    amended_value: float
    total_costs: float
    total_invoiced: float
    pending_invoices: float
    unpaid_invoices: float
    projected_margin: float
    margin_percentage: float
    progress_percentage: float
    status: JobStatus
    
    # Expense breakdown by category
    material_costs: float = 0.0
    labour_costs: float = 0.0
    plant_machinery_costs: float = 0.0
    overhead_costs: float = 0.0
    subcontractor_costs: float = 0.0
    
    # Budget vs actual comparison
    budget_variance: float = 0.0  # Positive means under budget, negative means over budget
    
class AlertResponse(BaseModel):
    id: int
    job_id: int
    alert_type: str
    message: str
    severity: str
    is_acknowledged: bool
    created_at: datetime
    
    class Config:
        from_attributes = True