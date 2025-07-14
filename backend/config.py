import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nda_dashboard.db")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Email Configuration for Budget Alerts
EMAIL_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "email_username": os.getenv("EMAIL_USERNAME", ""),
    "email_password": os.getenv("EMAIL_PASSWORD", ""),
    "from_email": os.getenv("FROM_EMAIL", ""),
    "enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true"
}

# Budget Alert Configuration
BUDGET_ALERT_CONFIG = {
    "default_threshold": 80,  # Default 80% threshold
    "check_frequency": 24,    # Check every 24 hours
    "alert_recipients": [
        "john.moran@nda.co.uk",
        "koyyana@nda.co.uk"
    ]
}

# File Upload Configuration
UPLOAD_CONFIG = {
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_extensions": [".xlsx", ".xls", ".csv"],
    "upload_directories": {
        "pnl": "PnL_Uploads",
        "invoices": "Invoice_Uploads",
        "cvr": "CVR_Templates"
    }
}

# CVR Processing Configuration
CVR_CONFIG = {
    "expected_sheets": ["Job Summary", "Financial Data", "Progress Tracking"],
    "required_columns": {
        "Job Summary": ["Job Code", "Job Name", "Client", "Contract Value"],
        "Financial Data": ["Job Code", "Invoiced", "Costs", "Margin"],
        "Progress Tracking": ["Job Code", "Progress %", "Expected Completion"]
    }
}

# Application Configuration
APP_CONFIG = {
    "app_name": "NDA Dashboard",
    "version": "1.0.0",
    "debug": os.getenv("DEBUG", "false").lower() == "true",
    "cors_origins": [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
}

# Role-based Access Configuration
ROLE_PERMISSIONS = {
    "admin": ["all"],
    "staff": [
        "view_dashboard",
        "create_jobs",
        "create_variations",
        "upload_files",
        "manage_budgets",
        "view_reports"
    ],
    "client": [
        "view_dashboard",
        "approve_variations",
        "view_reports"
    ]
}

# QuickBooks Data Mapping
QUICKBOOKS_MAPPING = {
    "pnl_columns": {
        "job_code": "Class",
        "expense_category": "Account",
        "amount": "Amount",
        "date": "Date",
        "description": "Description"
    },
    "invoice_columns": {
        "job_code": "Class",
        "invoice_number": "Invoice Number",
        "amount": "Amount",
        "date": "Date",
        "customer": "Customer",
        "paid": "Paid"
    },
    "expense_categories": {
        "Materials": ["Materials", "Supplies", "Equipment Purchase"],
        "Labour": ["Labour", "Wages", "Payroll"],
        "Plant": ["Plant Hire", "Machinery", "Equipment Rental", "Vehicle Costs"],
        "Overheads": ["Office Expenses", "Insurance", "Utilities", "Professional Fees"]
    }
}