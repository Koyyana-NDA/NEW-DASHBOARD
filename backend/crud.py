# backend/crud.py - Enhanced CRUD Operations for Dashboard Functionality

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from . import models
from .models import (
    Job, Expense, Invoice, Variation, Budget, Alert, User,
    JobCreate, JobUpdate, ExpenseCreate, InvoiceCreate, 
    VariationCreate, VariationUpdate, BudgetCreate,
    ExpenseCategory, JobStatus, VariationStatus
)

# Configure logging to help track operations
logger = logging.getLogger(__name__)

# ================================
# USER MANAGEMENT OPERATIONS
# ================================

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Retrieve a user by their username - essential for authentication
    This function acts like a directory lookup in your company's employee database
    """
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, hashed_password: str, role: str, email: str) -> User:
    """
    Create a new user account with role-based access control
    This enables you to add new team members with appropriate permissions
    """
    db_user = User(
        username=username,
        hashed_password=hashed_password,
        role=role,
        email=email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ================================
# JOB/PROJECT MANAGEMENT OPERATIONS
# ================================

def create_job(db: Session, job: JobCreate) -> Job:
    """
    Create a new job/project record
    This is like opening a new project file in your filing system
    """
    db_job = Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    logger.info(f"Created new job: {db_job.job_code}")
    return db_job

def get_job_by_code(db: Session, job_code: str) -> Optional[Job]:
    """
    Retrieve a specific job by its unique code
    Think of this as looking up a project by its file number
    """
    return db.query(Job).filter(Job.job_code == job_code).first()

def get_job_by_id(db: Session, job_id: int) -> Optional[Job]:
    """
    Retrieve a job by its database ID
    This is useful when you know the internal system ID
    """
    return db.query(Job).filter(Job.id == job_id).first()

def get_all_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[Job]:
    """
    Retrieve all jobs with pagination support
    This gives you a complete overview of all projects in your system
    """
    return db.query(Job).offset(skip).limit(limit).all()

def update_job(db: Session, job_id: int, job_update: JobUpdate) -> Optional[Job]:
    """
    Update an existing job's information
    This allows you to modify project details as circumstances change
    """
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        return None
    
    # Update only the fields that are provided
    update_data = job_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db_job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_job)
    return db_job

def delete_job(db: Session, job_id: int) -> bool:
    """
    Delete a job and all associated records
    Use this carefully - it's like shredding a complete project file
    """
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        return False
    
    # Delete associated records first (maintain referential integrity)
    db.query(Expense).filter(Expense.job_id == job_id).delete()
    db.query(Invoice).filter(Invoice.job_id == job_id).delete()
    db.query(Variation).filter(Variation.job_id == job_id).delete()
    db.query(Budget).filter(Budget.job_id == job_id).delete()
    db.query(Alert).filter(Alert.job_id == job_id).delete()
    
    db.delete(db_job)
    db.commit()
    return True

# ================================
# EXPENSE MANAGEMENT OPERATIONS
# ================================

def create_expense(db: Session, expense: ExpenseCreate) -> Expense:
    """
    Record a new expense against a job
    This is like adding a receipt to your project expense file
    """
    db_expense = Expense(**expense.dict())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def get_expenses_by_job(db: Session, job_id: int) -> List[Expense]:
    """
    Retrieve all expenses for a specific job
    This gives you a complete cost breakdown for a project
    """
    return db.query(Expense).filter(Expense.job_id == job_id).all()

def get_expenses_by_category(db: Session, job_id: int, category: ExpenseCategory) -> List[Expense]:
    """
    Retrieve expenses for a specific category within a job
    This helps you analyze spending patterns by type (material, labour, etc.)
    """
    return db.query(Expense).filter(
        and_(Expense.job_id == job_id, Expense.category == category)
    ).all()

def get_total_expenses_by_job(db: Session, job_id: int) -> float:
    """
    Calculate total expenses for a job
    This gives you the current total cost incurred on a project
    """
    result = db.query(func.sum(Expense.amount)).filter(Expense.job_id == job_id).scalar()
    return result if result else 0.0

def get_expenses_by_category_summary(db: Session, job_id: int) -> Dict[str, float]:
    """
    Get expense summary grouped by category
    This creates a breakdown showing how much you've spent on materials, labour, etc.
    """
    results = db.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(Expense.job_id == job_id).group_by(Expense.category).all()
    
    return {result.category.value: result.total for result in results}

# ================================
# INVOICE MANAGEMENT OPERATIONS
# ================================

def create_invoice(db: Session, invoice: InvoiceCreate) -> Invoice:
    """
    Create a new invoice record
    This is like issuing a bill to your client
    """
    db_invoice = Invoice(**invoice.dict())
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def get_invoices_by_job(db: Session, job_id: int) -> List[Invoice]:
    """
    Retrieve all invoices for a specific job
    This shows your complete billing history for a project
    """
    return db.query(Invoice).filter(Invoice.job_id == job_id).all()

def get_total_invoiced_by_job(db: Session, job_id: int) -> float:
    """
    Calculate total amount invoiced for a job
    This tells you how much revenue you've billed for a project
    """
    result = db.query(func.sum(Invoice.amount)).filter(Invoice.job_id == job_id).scalar()
    return result if result else 0.0

def get_unpaid_invoices_by_job(db: Session, job_id: int) -> List[Invoice]:
    """
    Get all unpaid invoices for a job
    This shows what money is still owed to you
    """
    return db.query(Invoice).filter(
        and_(Invoice.job_id == job_id, Invoice.is_paid == False)
    ).all()

def get_total_unpaid_by_job(db: Session, job_id: int) -> float:
    """
    Calculate total unpaid amount for a job
    This tells you how much outstanding money you're waiting to receive
    """
    result = db.query(func.sum(Invoice.amount)).filter(
        and_(Invoice.job_id == job_id, Invoice.is_paid == False)
    ).scalar()
    return result if result else 0.0

def mark_invoice_paid(db: Session, invoice_id: int, payment_reference: str = None) -> Optional[Invoice]:
    """
    Mark an invoice as paid
    This updates your records when a client pays their bill
    """
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not db_invoice:
        return None
    
    db_invoice.is_paid = True
    db_invoice.paid_date = datetime.utcnow()
    if payment_reference:
        db_invoice.payment_reference = payment_reference
    
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def get_overdue_invoices(db: Session, job_id: int = None) -> List[Invoice]:
    """
    Get invoices that are past their due date
    This helps you identify which clients need payment reminders
    """
    query = db.query(Invoice).filter(
        and_(Invoice.is_paid == False, Invoice.due_date < datetime.utcnow())
    )
    
    if job_id:
        query = query.filter(Invoice.job_id == job_id)
    
    return query.all()

# ================================
# VARIATION MANAGEMENT OPERATIONS
# ================================

def create_variation(db: Session, variation: VariationCreate) -> Variation:
    """
    Create a new variation request
    This is like requesting additional work approval from your client
    """
    db_variation = Variation(**variation.dict())
    db.add(db_variation)
    db.commit()
    db.refresh(db_variation)
    return db_variation

def get_variations_by_job(db: Session, job_id: int) -> List[Variation]:
    """
    Retrieve all variations for a specific job
    This shows all the additional work requests for a project
    """
    return db.query(Variation).filter(Variation.job_id == job_id).all()

def update_variation(db: Session, variation_id: int, variation_update: VariationUpdate) -> Optional[Variation]:
    """
    Update a variation (usually to change status to approved/rejected)
    This is how you process client responses to your additional work requests
    """
    db_variation = db.query(Variation).filter(Variation.id == variation_id).first()
    if not db_variation:
        return None
    
    update_data = variation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_variation, field, value)
    
    # Set approval date if status is being changed to approved
    if variation_update.status == VariationStatus.approved:
        db_variation.approved_date = datetime.utcnow()
    
    db.commit()
    db.refresh(db_variation)
    return db_variation

def get_approved_variations_total(db: Session, job_id: int) -> float:
    """
    Calculate total value of approved variations for a job
    This tells you how much additional work has been approved
    """
    result = db.query(func.sum(Variation.amount)).filter(
        and_(Variation.job_id == job_id, Variation.status == VariationStatus.approved)
    ).scalar()
    return result if result else 0.0

def get_pending_variations(db: Session, job_id: int = None) -> List[Variation]:
    """
    Get variations awaiting approval
    This shows what additional work requests are pending client response
    """
    query = db.query(Variation).filter(Variation.status == VariationStatus.pending)
    
    if job_id:
        query = query.filter(Variation.job_id == job_id)
    
    return query.all()

# ================================
# BUDGET MANAGEMENT OPERATIONS
# ================================

def create_budget(db: Session, budget: BudgetCreate) -> Budget:
    """
    Create a budget allocation for a job category
    This is like setting spending limits for different aspects of your project
    """
    db_budget = Budget(**budget.dict())
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

def get_budgets_by_job(db: Session, job_id: int) -> List[Budget]:
    """
    Retrieve all budget allocations for a job
    This shows your planned spending breakdown for a project
    """
    return db.query(Budget).filter(Budget.job_id == job_id).all()

def update_budget(db: Session, budget_id: int, new_amount: float) -> Optional[Budget]:
    """
    Update a budget allocation
    This allows you to revise your spending limits as project needs change
    """
    db_budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not db_budget:
        return None
    
    db_budget.budgeted_amount = new_amount
    db_budget.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_budget)
    return db_budget

def check_budget_overruns(db: Session, job_id: int) -> List[Dict[str, Any]]:
    """
    Check if any expense categories have exceeded their budgets
    This is your early warning system for cost overruns
    """
    budgets = get_budgets_by_job(db, job_id)
    overruns = []
    
    for budget in budgets:
        actual_spend = db.query(func.sum(Expense.amount)).filter(
            and_(Expense.job_id == job_id, Expense.category == budget.category)
        ).scalar() or 0.0
        
        if actual_spend > budget.budgeted_amount:
            overruns.append({
                'category': budget.category.value,
                'budgeted': budget.budgeted_amount,
                'actual': actual_spend,
                'overrun': actual_spend - budget.budgeted_amount,
                'percentage_over': ((actual_spend - budget.budgeted_amount) / budget.budgeted_amount) * 100
            })
    
    return overruns

# ================================
# DASHBOARD METRICS OPERATIONS
# ================================

def get_dashboard_metrics(db: Session, job_id: int = None) -> Dict[str, Any]:
    """
    Calculate comprehensive dashboard metrics
    This is your financial command center - all key numbers in one place
    """
    # Base query - either for specific job or all jobs
    if job_id:
        jobs = db.query(Job).filter(Job.id == job_id).all()
    else:
        jobs = db.query(Job).all()
    
    if not jobs:
        return {
            'total_contract_value': 0.0,
            'total_invoiced': 0.0,
            'total_costs': 0.0,
            'projected_margin': 0.0,
            'pending_invoices': 0.0,
            'unpaid_invoices': 0.0,
            'active_jobs_count': 0,
            'completed_jobs_count': 0
        }
    
    # Calculate aggregated metrics
    total_contract_value = sum(job.amended_value for job in jobs)
    total_costs = sum(get_total_expenses_by_job(db, job.id) for job in jobs)
    total_invoiced = sum(get_total_invoiced_by_job(db, job.id) for job in jobs)
    total_unpaid = sum(get_total_unpaid_by_job(db, job.id) for job in jobs)
    
    # Calculate pending invoices (work done but not yet invoiced)
    # This is estimated as (costs incurred + reasonable margin) - already invoiced
    pending_invoices = max(0, (total_costs * 1.2) - total_invoiced)  # Assuming 20% margin
    
    projected_margin = total_contract_value - total_costs
    
    # Count jobs by status
    active_jobs = sum(1 for job in jobs if job.status == JobStatus.active)
    completed_jobs = sum(1 for job in jobs if job.status == JobStatus.completed)
    
    return {
        'total_contract_value': total_contract_value,
        'total_invoiced': total_invoiced,
        'total_costs': total_costs,
        'projected_margin': projected_margin,
        'pending_invoices': pending_invoices,
        'unpaid_invoices': total_unpaid,
        'active_jobs_count': active_jobs,
        'completed_jobs_count': completed_jobs
    }

def get_job_detail_metrics(db: Session, job_id: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed metrics for a specific job
    This provides comprehensive financial analysis for individual projects
    """
    job = get_job_by_id(db, job_id)
    if not job:
        return None
    
    # Get expense breakdown by category
    expense_summary = get_expenses_by_category_summary(db, job_id)
    
    # Calculate key metrics
    total_costs = get_total_expenses_by_job(db, job_id)
    total_invoiced = get_total_invoiced_by_job(db, job_id)
    unpaid_invoices = get_total_unpaid_by_job(db, job_id)
    approved_variations = get_approved_variations_total(db, job_id)
    
    # Update amended value with approved variations
    current_contract_value = job.contract_value + approved_variations
    
    # Calculate projected margin
    projected_margin = current_contract_value - job.estimated_final_cost
    margin_percentage = (projected_margin / current_contract_value * 100) if current_contract_value > 0 else 0
    
    # Calculate pending invoices (work done but not yet billed)
    pending_invoices = max(0, total_costs - total_invoiced)
    
    # Get budget variance
    budgets = get_budgets_by_job(db, job_id)
    total_budget = sum(budget.budgeted_amount for budget in budgets)
    budget_variance = total_budget - total_costs
    
    return {
        'job_code': job.job_code,
        'job_name': job.job_name,
        'client': job.client,
        'contract_value': job.contract_value,
        'amended_value': current_contract_value,
        'total_costs': total_costs,
        'total_invoiced': total_invoiced,
        'pending_invoices': pending_invoices,
        'unpaid_invoices': unpaid_invoices,
        'projected_margin': projected_margin,
        'margin_percentage': margin_percentage,
        'progress_percentage': job.progress_percentage,
        'status': job.status,
        
        # Expense breakdown by category
        'material_costs': expense_summary.get('material', 0.0),
        'labour_costs': expense_summary.get('labour', 0.0),
        'plant_machinery_costs': expense_summary.get('plant_machinery', 0.0),
        'overhead_costs': expense_summary.get('overheads', 0.0),
        'subcontractor_costs': expense_summary.get('subcontractor', 0.0),
        
        # Budget comparison
        'budget_variance': budget_variance,
        'total_budget': total_budget
    }

# ================================
# ALERT MANAGEMENT OPERATIONS
# ================================

def create_alert(db: Session, job_id: int, alert_type: str, message: str, severity: str = "medium") -> Alert:
    """
    Create a new alert for budget overruns, overdue invoices, etc.
    This is your notification system for important events requiring attention
    """
    db_alert = Alert(
        job_id=job_id,
        alert_type=alert_type,
        message=message,
        severity=severity
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

def get_active_alerts(db: Session, job_id: int = None) -> List[Alert]:
    """
    Get all unacknowledged alerts
    This shows what issues need immediate attention
    """
    query = db.query(Alert).filter(Alert.is_acknowledged == False)
    
    if job_id:
        query = query.filter(Alert.job_id == job_id)
    
    return query.order_by(Alert.created_at.desc()).all()

def acknowledge_alert(db: Session, alert_id: int, acknowledged_by: str) -> Optional[Alert]:
    """
    Mark an alert as acknowledged
    This is how you indicate that you've seen and addressed an issue
    """
    db_alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not db_alert:
        return None
    
    db_alert.is_acknowledged = True
    db_alert.acknowledged_at = datetime.utcnow()
    db_alert.acknowledged_by = acknowledged_by
    
    db.commit()
    db.refresh(db_alert)
    return db_alert

def check_and_create_budget_alerts(db: Session, job_id: int) -> List[Alert]:
    """
    Check for budget overruns and create alerts if necessary
    This is your automated monitoring system that watches for spending issues
    """
    overruns = check_budget_overruns(db, job_id)
    created_alerts = []
    
    for overrun in overruns:
        # Check if we already have an active alert for this overrun
        existing_alert = db.query(Alert).filter(
            and_(
                Alert.job_id == job_id,
                Alert.alert_type == "budget_overrun",
                Alert.message.contains(overrun['category']),
                Alert.is_acknowledged == False
            )
        ).first()
        
        if not existing_alert:
            # Create new alert
            message = f"Budget overrun in {overrun['category']}: £{overrun['overrun']:.2f} over budget ({overrun['percentage_over']:.1f}%)"
            severity = "high" if overrun['percentage_over'] > 20 else "medium"
            
            alert = create_alert(db, job_id, "budget_overrun", message, severity)
            created_alerts.append(alert)
    
    return created_alerts

def check_and_create_invoice_alerts(db: Session, job_id: int = None) -> List[Alert]:
    """
    Check for overdue invoices and create alerts
    This monitors your cash flow and highlights payment issues
    """
    overdue_invoices = get_overdue_invoices(db, job_id)
    created_alerts = []
    
    for invoice in overdue_invoices:
        # Check if we already have an active alert for this invoice
        existing_alert = db.query(Alert).filter(
            and_(
                Alert.job_id == invoice.job_id,
                Alert.alert_type == "overdue_invoice",
                Alert.message.contains(invoice.invoice_number),
                Alert.is_acknowledged == False
            )
        ).first()
        
        if not existing_alert:
            days_overdue = (datetime.utcnow() - invoice.due_date).days
            message = f"Invoice {invoice.invoice_number} is {days_overdue} days overdue (£{invoice.amount:.2f})"
            severity = "high" if days_overdue > 30 else "medium"
            
            alert = create_alert(db, invoice.job_id, "overdue_invoice", message, severity)
            created_alerts.append(alert)
    
    return created_alerts

# ================================
# BULK DATA OPERATIONS
# ================================

def bulk_create_expenses(db: Session, expenses: List[ExpenseCreate]) -> List[Expense]:
    """
    Create multiple expenses at once (useful for P&L import)
    This is like processing a batch of receipts all at once
    """
    db_expenses = [Expense(**expense.dict()) for expense in expenses]
    db.add_all(db_expenses)
    db.commit()
    
    # Refresh all objects to get their IDs
    for expense in db_expenses:
        db.refresh(expense)
    
    return db_expenses

def bulk_create_invoices(db: Session, invoices: List[InvoiceCreate]) -> List[Invoice]:
    """
    Create multiple invoices at once (useful for invoice report import)
    This is like processing a batch of bills all at once
    """
    db_invoices = [Invoice(**invoice.dict()) for invoice in invoices]
    db.add_all(db_invoices)
    db.commit()
    
    # Refresh all objects to get their IDs
    for invoice in db_invoices:
        db.refresh(invoice)
    
    return db_invoices

def get_jobs_summary(db: Session) -> List[Dict[str, Any]]:
    """
    Get a summary of all jobs with key metrics
    This provides your overview dashboard showing all projects at a glance
    """
    jobs = get_all_jobs(db)
    summary = []
    
    for job in jobs:
        metrics = get_job_detail_metrics(db, job.id)
        if metrics:
            summary.append({
                'id': job.id,
                'job_code': job.job_code,
                'job_name': job.job_name,
                'client': job.client,
                'status': job.status.value,
                'progress_percentage': job.progress_percentage,
                'contract_value': metrics['amended_value'],
                'total_costs': metrics['total_costs'],
                'projected_margin': metrics['projected_margin'],
                'margin_percentage': metrics['margin_percentage'],
                'unpaid_invoices': metrics['unpaid_invoices']
            })
    
    return summary

# ================================
# SEARCH AND FILTER OPERATIONS
# ================================

def search_jobs(db: Session, query: str) -> List[Job]:
    """
    Search jobs by code, name, or client
    This helps you quickly find specific projects
    """
    return db.query(Job).filter(
        or_(
            Job.job_code.ilike(f"%{query}%"),
            Job.job_name.ilike(f"%{query}%"),
            Job.client.ilike(f"%{query}%")
        )
    ).all()

def get_jobs_by_status(db: Session, status: JobStatus) -> List[Job]:
    """
    Get all jobs with a specific status
    This helps you focus on projects in particular stages
    """
    return db.query(Job).filter(Job.status == status).all()

def get_jobs_by_client(db: Session, client: str) -> List[Job]:
    """
    Get all jobs for a specific client
    This helps you analyze your relationship with individual clients
    """
    return db.query(Job).filter(Job.client.ilike(f"%{client}%")).all()

def get_financial_summary_by_period(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Get financial summary for a specific time period
    This helps you analyze performance over specific timeframes
    """
    # Get expenses in the period
    expenses = db.query(Expense).filter(
        and_(Expense.expense_date >= start_date, Expense.expense_date <= end_date)
    ).all()
    
    # Get invoices in the period
    invoices = db.query(Invoice).filter(
        and_(Invoice.invoice_date >= start_date, Invoice.invoice_date <= end_date)
    ).all()
    
    total_expenses = sum(expense.amount for expense in expenses)
    total_invoiced = sum(invoice.amount for invoice in invoices)
    
    # Group expenses by category
    expense_by_category = {}
    for expense in expenses:
        category = expense.category.value
        expense_by_category[category] = expense_by_category.get(category, 0) + expense.amount
    
    return {
        'period_start': start_date,
        'period_end': end_date,
        'total_expenses': total_expenses,
        'total_invoiced': total_invoiced,
        'net_margin': total_invoiced - total_expenses,
        'expense_by_category': expense_by_category,
        'invoice_count': len(invoices),
        'expense_count': len(expenses)
    }