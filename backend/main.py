

from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
# from pydantic import Basemodel
from datetime import datetime
import logging
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import io
import os


# Import your existing modules

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app (if not already created in your main.py)
app = FastAPI(title="NDA Dashboard API", version="1.0.0")

const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors({
  origin: 'https://new-dashboard-u2l9.onrender.com',
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type']
}));

app.use(express.urlencoded({ extended: true })); // Parse URL-encoded bodies

app.post('/token', (req, res) => {
  const { username, password } = req.body;
  // Validate credentials and return token
  res.json({ token: 'example-token' });
});

from .auth import router as auth_router
from .utils.budget_check import BudgetChecker
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from fastapi.responses import FileResponse
from .utils.update_cvr import process_all_jobs_cvr, download_latest_cvr
# import pandas as pd
from .database import get_db
from .auth import get_current_user, oauth2_scheme
from .models import *
from . import crud

app.include_router(auth_router, tags=["Authentication"])


# Security scheme
# security = HTTPBearer()

# ================================
# DASHBOARD OVERVIEW ENDPOINTS
# ================================

@app.get("/api/dashboard/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get overall dashboard metrics - this is your main command center view
    Think of this as the executive summary that gives you the big picture
    """
    try:
        # Get comprehensive metrics for all jobs
        metrics = crud.get_dashboard_metrics(db)
        
        # Get jobs summary for the overview table
        jobs_summary = crud.get_jobs_summary(db)
        
        # Get active alerts that need attention
        alerts = crud.get_active_alerts(db)
        
        # Check for any new budget or invoice alerts
        all_jobs = crud.get_all_jobs(db)
        for job in all_jobs:
            crud.check_and_create_budget_alerts(db, job.id)
            crud.check_and_create_invoice_alerts(db, job.id)
        
        # Get updated alerts after checking
        alerts = crud.get_active_alerts(db)
        
        return {
            "success": True,
            "data": {
                "metrics": metrics,
                "jobs_summary": jobs_summary,
                "alerts": [
                    {
                        "id": alert.id,
                        "job_id": alert.job_id,
                        "type": alert.alert_type,
                        "message": alert.message,
                        "severity": alert.severity,
                        "created_at": alert.created_at.isoformat()
                    }
                    for alert in alerts
                ],
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")

@app.get("/api/dashboard/jobs")
async def get_all_jobs_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all jobs for dropdown selection
    This populates your job selection dropdown in the dashboard
    """
    try:
        jobs = crud.get_all_jobs(db)
        return {
            "success": True,
            "data": [
                {
                    "id": job.id,
                    "job_code": job.job_code,
                    "job_name": job.job_name,
                    "client": job.client,
                    "status": job.status.value
                }
                for job in jobs
            ]
        }
    except Exception as e:
        logger.error(f"Error getting jobs list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@app.get("/api/dashboard/job/{job_id}")
async def get_job_details(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific job
    This provides comprehensive financial analysis for individual projects
    """
    try:
        # Get job basic info
        job = crud.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get detailed metrics
        metrics = crud.get_job_detail_metrics(db, job_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Job metrics not found")
        
        # Get expenses breakdown
        expenses = crud.get_expenses_by_job(db, job_id)
        expense_summary = crud.get_expenses_by_category_summary(db, job_id)
        
        # Get invoices information
        invoices = crud.get_invoices_by_job(db, job_id)
        unpaid_invoices = crud.get_unpaid_invoices_by_job(db, job_id)
        
        # Get variations
        variations = crud.get_variations_by_job(db, job_id)
        
        # Get budget information
        budgets = crud.get_budgets_by_job(db, job_id)
        
        # Get job-specific alerts
        alerts = crud.get_active_alerts(db, job_id)
        
        return {
            "success": True,
            "data": {
                "job_info": {
                    "id": job.id,
                    "job_code": job.job_code,
                    "job_name": job.job_name,
                    "client": job.client,
                    "status": job.status.value,
                    "progress_percentage": job.progress_percentage,
                    "start_date": job.start_date.isoformat() if job.start_date else None,
                    "expected_completion": job.expected_completion_date.isoformat() if job.expected_completion_date else None
                },
                "metrics": metrics,
                "expenses": {
                    "total": len(expenses),
                    "by_category": expense_summary,
                    "recent": [
                        {
                            "id": expense.id,
                            "category": expense.category.value,
                            "description": expense.description,
                            "amount": expense.amount,
                            "date": expense.expense_date.isoformat()
                        }
                        for expense in sorted(expenses, key=lambda x: x.expense_date, reverse=True)[:10]
                    ]
                },
                "invoices": {
                    "total_count": len(invoices),
                    "unpaid_count": len(unpaid_invoices),
                    "recent": [
                        {
                            "id": invoice.id,
                            "invoice_number": invoice.invoice_number,
                            "amount": invoice.amount,
                            "date": invoice.invoice_date.isoformat(),
                            "due_date": invoice.due_date.isoformat(),
                            "is_paid": invoice.is_paid
                        }
                        for invoice in sorted(invoices, key=lambda x: x.invoice_date, reverse=True)[:10]
                    ]
                },
                "variations": [
                    {
                        "id": var.id,
                        "variation_number": var.variation_number,
                        "description": var.description,
                        "amount": var.amount,
                        "status": var.status.value,
                        "submitted_date": var.submitted_date.isoformat(),
                        "approved_date": var.approved_date.isoformat() if var.approved_date else None
                    }
                    for var in variations
                ],
                "budgets": [
                    {
                        "id": budget.id,
                        "category": budget.category.value,
                        "budgeted_amount": budget.budgeted_amount,
                        "actual_spent": expense_summary.get(budget.category.value, 0.0),
                        "variance": budget.budgeted_amount - expense_summary.get(budget.category.value, 0.0)
                    }
                    for budget in budgets
                ],
                "alerts": [
                    {
                        "id": alert.id,
                        "type": alert.alert_type,
                        "message": alert.message,
                        "severity": alert.severity,
                        "created_at": alert.created_at.isoformat()
                    }
                    for alert in alerts
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching job details: {str(e)}")

# ================================
# FILE UPLOAD AND PROCESSING ENDPOINTS
# ================================

@app.post("/api/upload/pnl")
async def upload_pnl_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process P&L report from QuickBooks
    This is like feeding your financial data into the system for analysis
    """
    try:
        # Verify file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Please upload an Excel file (.xlsx or .xls)")
        
        # Read the uploaded file
        contents = await file.read()
        
        # Save uploaded file for reference
        import os
        os.makedirs("PnL_Uploads", exist_ok=True)
        file_path = f"PnL_Uploads/pnl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Process the P&L file (you'll need to implement this based on your QuickBooks format)
        from .utils.parse_pnl import process_pnl_file
        processed_data = process_pnl_file(file_path, db)
        
        return {
            "success": True,
            "message": f"P&L report processed successfully. {processed_data['expenses_created']} expenses added.",
            "data": {
                "file_name": file.filename,
                "processed_at": datetime.utcnow().isoformat(),
                "summary": processed_data
            }
        }
    except Exception as e:
        logger.error(f"Error processing P&L file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing P&L file: {str(e)}")

@app.post("/api/upload/invoices")
async def upload_invoices_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process invoice report from QuickBooks
    This updates your revenue and payment tracking information
    """
    try:
        # Verify file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Please upload an Excel file (.xlsx or .xls)")
        
        # Read the uploaded file
        contents = await file.read()
        
        # Save uploaded file for reference
        import os
        os.makedirs("Invoice_Uploads", exist_ok=True)
        file_path = f"Invoice_Uploads/invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Process the invoice file
        from .utils.parse_invoice import process_invoice_file
        processed_data = process_invoice_file(file_path, db)
        
        return {
            "success": True,
            "message": f"Invoice report processed successfully. {processed_data['invoices_created']} invoices added/updated.",
            "data": {
                "file_name": file.filename,
                "processed_at": datetime.utcnow().isoformat(),
                "summary": processed_data
            }
        }
    except Exception as e:
        logger.error(f"Error processing invoice file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing invoice file: {str(e)}")

@app.post("/api/upload/cvr")
async def upload_cvr_template(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload CVR template file
    This is your master project tracking template
    """
    try:
        # Verify file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Please upload an Excel file (.xlsx or .xls)")
        
        # Read the uploaded file
        contents = await file.read()
        
        # Save as master CVR template
        import os
        os.makedirs("CVR_Templates", exist_ok=True)
        file_path = f"CVR_Templates/cvr_master_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Process and validate CVR structure
        from .utils.update_cvr import validate_cvr_structure
        validation_result = validate_cvr_structure(file_path)
        
        return {
            "success": True,
            "message": "CVR template uploaded successfully",
            "data": {
                "file_name": file.filename,
                "uploaded_at": datetime.utcnow().isoformat(),
                "validation": validation_result
            }
        }
    except Exception as e:
        logger.error(f"Error uploading CVR template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading CVR template: {str(e)}")
@app.post("/api/cvr/process", tags=["CVR"])
def run_cvr_processing(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger the CVR auto‐update engine. Returns processed file name.
    """
    result = process_all_jobs_cvr(db)
    return {"success": True, "processed_file": result["file"]}

@app.get("/api/cvr/download", tags=["CVR"])
def get_processed_cvr(
    current_user: User = Depends(get_current_user)
):
    """
    Download the most recently processed CVR.
    """
    path = download_latest_cvr()
    return FileResponse(path, filename=os.path.basename(path), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ================================
# BUDGET MANAGEMENT ENDPOINTS
# ================================

@app.post("/api/budget/create")
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new budget allocation for a job category
    This sets your spending limits for different aspects of a project
    """
    try:
        # Verify job exists
        job = crud.get_job_by_id(db, budget_data.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if budget already exists for this job/category combination
        existing_budgets = crud.get_budgets_by_job(db, budget_data.job_id)
        for existing in existing_budgets:
            if existing.category == budget_data.category:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Budget already exists for {budget_data.category.value} in this job"
                )
        
        budget = crud.create_budget(db, budget_data)
        
        return {
            "success": True,
            "message": "Budget created successfully",
            "data": {
                "id": budget.id,
                "job_id": budget.job_id,
                "category": budget.category.value,
                "budgeted_amount": budget.budgeted_amount,
                "created_at": budget.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating budget: {str(e)}")

@app.put("/api/budget/{budget_id}")
async def update_budget(
    budget_id: int,
    new_amount: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a budget allocation
    This allows you to revise spending limits as project needs change
    """
    try:
        budget = crud.update_budget(db, budget_id, new_amount)
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        
        return {
            "success": True,
            "message": "Budget updated successfully",
            "data": {
                "id": budget.id,
                "category": budget.category.value,
                "budgeted_amount": budget.budgeted_amount,
                "updated_at": budget.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating budget: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating budget: {str(e)}")

@app.get("/api/budget/overruns/{job_id}")
async def get_budget_overruns(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get budget overruns for a specific job
    This is your early warning system for cost overruns
    """
    try:
        job = crud.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        overruns = crud.check_budget_overruns(db, job_id)
        
        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "job_code": job.job_code,
                "overruns": overruns
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting budget overruns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting budget overruns: {str(e)}")

# ================================
# VARIATION MANAGEMENT ENDPOINTS
# ================================
@app.post("/api/variation/create")
async def create_variation(
    variation_data: VariationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new variation for a job
    This allows you to track changes and additions to the original contract
    """
    try:
        # Verify job exists
        job = crud.get_job_by_id(db, variation_data.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Only admin and staff can create variations
        if current_user.role not in [UserRole.admin, UserRole.staff]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        variation = crud.create_variation(db, variation_data)
        
        return {
            "success": True,
            "message": "Variation created successfully",
            "data": {
                "id": variation.id,
                "job_id": variation.job_id,
                "variation_number": variation.variation_number,
                "description": variation.description,
                "amount": variation.amount,
                "status": variation.status.value,
                "submitted_date": variation.submitted_date.isoformat(),
                "submitted_by": variation.submitted_by
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating variation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating variation: {str(e)}")

@app.put("/api/variation/{variation_id}/approve")
async def approve_variation(
    variation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a variation - typically done by client users
    This formally accepts the variation and includes it in financial projections
    """
    try:
        # Only admin and client users can approve variations
        if current_user.role not in [UserRole.admin, UserRole.client]:
            raise HTTPException(status_code=403, detail="Only admin or client users can approve variations")
        
        variation = crud.approve_variation(db, variation_id, current_user.username)
        if not variation:
            raise HTTPException(status_code=404, detail="Variation not found")
        
        return {
            "success": True,
            "message": "Variation approved successfully",
            "data": {
                "id": variation.id,
                "variation_number": variation.variation_number,
                "status": variation.status.value,
                "approved_date": variation.approved_date.isoformat(),
                "approved_by": variation.approved_by
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving variation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error approving variation: {str(e)}")

@app.put("/api/variation/{variation_id}/reject")
async def reject_variation(
    variation_id: int,
    rejection_reason: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a variation with a reason
    This formally declines the variation and removes it from financial projections
    """
    try:
        # Only admin and client users can reject variations
        if current_user.role not in [UserRole.admin, UserRole.client]:
            raise HTTPException(status_code=403, detail="Only admin or client users can reject variations")
        
        variation = crud.reject_variation(db, variation_id, current_user.username, rejection_reason)
        if not variation:
            raise HTTPException(status_code=404, detail="Variation not found")
        
        return {
            "success": True,
            "message": "Variation rejected successfully",
            "data": {
                "id": variation.id,
                "variation_number": variation.variation_number,
                "status": variation.status.value,
                "rejection_reason": variation.rejection_reason,
                "rejected_by": variation.rejected_by
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting variation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error rejecting variation: {str(e)}")

@app.get("/api/variation/{job_id}/pending")
async def get_pending_variations(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending variations for a specific job
    This shows variations that need client approval
    """
    try:
        job = crud.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        variations = crud.get_pending_variations_by_job(db, job_id)
        
        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "job_code": job.job_code,
                "pending_variations": [
                    {
                        "id": var.id,
                        "variation_number": var.variation_number,
                        "description": var.description,
                        "amount": var.amount,
                        "submitted_date": var.submitted_date.isoformat(),
                        "submitted_by": var.submitted_by
                    }
                    for var in variations
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pending variations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting pending variations: {str(e)}")

# ================================
# ALERTS AND NOTIFICATIONS ENDPOINTS
# ================================

@app.get("/api/alerts")
async def get_all_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active alerts across all jobs
    This is your central notification center
    """
    try:
        alerts = crud.get_active_alerts(db)
        
        return {
            "success": True,
            "data": [
                {
                    "id": alert.id,
                    "job_id": alert.job_id,
                    "job_code": alert.job.job_code if alert.job else None,
                    "type": alert.alert_type,
                    "message": alert.message,
                    "severity": alert.severity,
                    "created_at": alert.created_at.isoformat(),
                    "is_resolved": alert.is_resolved
                }
                for alert in alerts
            ]
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")

@app.put("/api/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark an alert as resolved
    This removes the alert from the active notifications
    """
    try:
        alert = crud.resolve_alert(db, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "success": True,
            "message": "Alert resolved successfully",
            "data": {
                "id": alert.id,
                "resolved_at": alert.resolved_at.isoformat(),
                "resolved_by": alert.resolved_by
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resolving alert: {str(e)}")

# ================================
# REPORTING ENDPOINTS
# ================================

@app.get("/api/reports/job-summary")
async def get_job_summary_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive job summary report
    This provides executive-level overview of all projects
    """
    try:
        jobs = crud.get_all_jobs(db)
        report_data = []
        
        for job in jobs:
            metrics = crud.get_job_detail_metrics(db, job.id)
            if metrics:
                report_data.append({
                    "job_code": job.job_code,
                    "job_name": job.job_name,
                    "client": job.client,
                    "status": job.status.value,
                    "progress": job.progress_percentage,
                    "contract_value": metrics.get("contract_value", 0),
                    "invoiced_amount": metrics.get("invoiced_amount", 0),
                    "total_costs": metrics.get("total_costs", 0),
                    "projected_margin": metrics.get("projected_margin", 0),
                    "margin_percentage": metrics.get("margin_percentage", 0)
                })
        
        return {
            "success": True,
            "data": {
                "report_date": datetime.utcnow().isoformat(),
                "total_jobs": len(report_data),
                "jobs": report_data
            }
        }
    except Exception as e:
        logger.error(f"Error generating job summary report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/api/reports/financial-summary")
async def get_financial_summary_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate financial summary report
    This provides comprehensive financial overview across all projects
    """
    try:
        metrics = crud.get_dashboard_metrics(db)
        
        # Get additional financial breakdowns
        jobs = crud.get_all_jobs(db)
        status_breakdown = {}
        client_breakdown = {}
        
        for job in jobs:
            # Status breakdown
            status = job.status.value
            if status not in status_breakdown:
                status_breakdown[status] = {"count": 0, "total_value": 0}
            status_breakdown[status]["count"] += 1
            
            # Client breakdown
            client = job.client
            if client not in client_breakdown:
                client_breakdown[client] = {"count": 0, "total_value": 0}
            client_breakdown[client]["count"] += 1
            
            # Add financial data
            job_metrics = crud.get_job_detail_metrics(db, job.id)
            if job_metrics:
                contract_value = job_metrics.get("contract_value", 0)
                status_breakdown[status]["total_value"] += contract_value
                client_breakdown[client]["total_value"] += contract_value
        
        return {
            "success": True,
            "data": {
                "report_date": datetime.utcnow().isoformat(),
                "overall_metrics": metrics,
                "status_breakdown": status_breakdown,
                "client_breakdown": client_breakdown
            }
        }
    except Exception as e:
        logger.error(f"Error generating financial summary report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

# ================================
# UTILITY ENDPOINTS
# ================================

@app.post("/api/jobs/create")
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new job/project
    This adds a new project to your portfolio
    """
    try:
        # Only admin and staff can create jobs
        if current_user.role not in [UserRole.admin, UserRole.staff]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        job = crud.create_job(db, job_data)
        
        return {
            "success": True,
            "message": "Job created successfully",
            "data": {
                "id": job.id,
                "job_code": job.job_code,
                "job_name": job.job_name,
                "client": job.client,
                "status": job.status.value,
                "created_at": job.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")

@app.put("/api/jobs/{job_id}/update-progress")
async def update_job_progress(
    job_id: int,
    progress_percentage: float = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update job progress percentage
    This tracks how much of the project is completed
    """
    try:
        if progress_percentage < 0 or progress_percentage > 100:
            raise HTTPException(status_code=400, detail="Progress percentage must be between 0 and 100")
        
        job = crud.update_job_progress(db, job_id, progress_percentage)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "success": True,
            "message": "Job progress updated successfully",
            "data": {
                "id": job.id,
                "job_code": job.job_code,
                "progress_percentage": job.progress_percentage,
                "updated_at": job.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating job progress: {str(e)}")

# Make sure to add the health check endpoint if not already present
@app.get("/api/health")
async def health_check():
    """
    Simple health check endpoint
    This confirms your API is running properly
    """
    return {
        "success": True,
        "message": "NDA Dashboard API is running",
        "timestamp": datetime.utcnow().isoformat()
    }

# ================================
# BUDGET MONITORING ENDPOINTS
# ================================

@app.post("/api/budget/check-all")
async def check_all_budgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check all budget thresholds and generate alerts
    This is your comprehensive budget monitoring system
    """
    try:
        budget_checker = BudgetChecker(db)
        results = budget_checker.check_all_budgets()
        
        return {
            "success": True,
            "message": f"Budget check completed. {len(results)} alerts generated.",
            "data": {
                "check_timestamp": datetime.utcnow().isoformat(),
                "alerts_generated": results
            }
        }
    except Exception as e:
        logger.error(f"Error checking budgets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking budgets: {str(e)}")

@app.post("/api/budget/check-job/{job_id}")
async def check_job_budget(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check budget for a specific job
    This monitors individual project budget compliance
    """
    try:
        job = crud.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        budget_checker = BudgetChecker(db)
        results = budget_checker.check_job_budget(job_id)
        
        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "job_code": job.job_code,
                "check_timestamp": datetime.utcnow().isoformat(),
                "budget_status": results
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking job budget: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking job budget: {str(e)}")

@app.post("/api/budget/set-threshold")
async def set_budget_threshold(
    job_id: int,
    category: str,
    threshold_percentage: float = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set budget alert threshold for a specific job category
    This customizes when you want to be warned about budget overruns
    """
    try:
        if threshold_percentage < 0 or threshold_percentage > 100:
            raise HTTPException(status_code=400, detail="Threshold must be between 0 and 100")
        
        job = crud.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        budget_checker = BudgetChecker(db)
        result = budget_checker.set_budget_threshold(job_id, category, threshold_percentage)
        
        return {
            "success": True,
            "message": f"Budget threshold set for {category} at {threshold_percentage}%",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting budget threshold: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting budget threshold: {str(e)}")

@app.get("/api/budget/status/{job_id}")
async def get_budget_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current budget status for a job
    This shows how much of each budget category has been used
    """
    try:
        job = crud.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        budget_checker = BudgetChecker(db)
        status = budget_checker.get_budget_status(job_id)
        
        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "job_code": job.job_code,
                "budget_status": status,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting budget status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting budget status: {str(e)}")

# ================================
# AUTOMATED BUDGET MONITORING
# ================================

@app.post("/api/budget/auto-check")
async def auto_budget_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Automated budget checking - call this after P&L uploads
    This automatically monitors budgets whenever new expenses are added
    """
    try:
        budget_checker = BudgetChecker(db)
        
        # Check all jobs for budget overruns
        all_jobs = crud.get_all_jobs(db)
        total_alerts = 0
        
        for job in all_jobs:
            alerts = budget_checker.check_job_budget(job.id)
            total_alerts += len(alerts)
        
        return {
            "success": True,
            "message": f"Automated budget check completed. {total_alerts} alerts generated.",
            "data": {
                "jobs_checked": len(all_jobs),
                "total_alerts": total_alerts,
                "check_timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error in automated budget check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in automated budget check: {str(e)}")
