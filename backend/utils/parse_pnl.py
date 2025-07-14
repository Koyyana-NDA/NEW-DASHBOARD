"""
P&L Report Parser - backend/utils/parse_pnl.py

This module is like a skilled translator who can read QuickBooks P&L reports
and convert them into a format your dashboard can understand and process.

Think of this as your financial data preprocessor - it takes the raw Excel
output from QuickBooks and transforms it into structured database records.
"""

import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from ..models import ExpenseCategory, JobStatus
from .. import crud

# Configure logging to track the parsing process
logger = logging.getLogger(__name__)

class PnLParser:
    """
    The PnLParser class acts like a specialized accountant who knows exactly
    how to read and interpret your QuickBooks P&L reports.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.processed_expenses = []
        self.errors = []
        self.job_mappings = {}
        
    def load_job_mappings(self):
        """
        Load existing job codes from database to match with P&L classes
        This is like creating a directory of all your active projects
        """
        try:
            jobs = crud.get_all_jobs(self.db)
            for job in jobs:
                self.job_mappings[job.job_code] = job.id
            logger.info(f"Loaded {len(self.job_mappings)} job mappings")
        except Exception as e:
            logger.error(f"Error loading job mappings: {str(e)}")
            self.errors.append(f"Failed to load job mappings: {str(e)}")
    
    def parse_excel_file(self, file_path: str) -> pd.DataFrame:
        """
        Read and parse the Excel file from QuickBooks
        This is like opening the financial report and preparing it for analysis
        """
        try:
            # Try different sheet names that QuickBooks might use
            possible_sheets = ['Profit & Loss by Class', 'P&L by Class', 'Sheet1', 0]
            
            df = None
            for sheet in possible_sheets:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet)
                    logger.info(f"Successfully loaded sheet: {sheet}")
                    break
                except Exception as e:
                    logger.warning(f"Could not load sheet {sheet}: {str(e)}")
                    continue
            
            if df is None:
                raise ValueError("Could not find a valid sheet in the Excel file")
            
            # Clean the dataframe
            df = df.dropna(how='all')  # Remove empty rows
            df = df.fillna(0)  # Replace NaN with 0
            
            return df
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {str(e)}")
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
    
    def categorize_expense(self, description: str) -> ExpenseCategory:
        """
        Categorize expenses based on their description
        This is like a smart filing system that knows which drawer each expense belongs in
        """
        description = description.lower().strip()
        
        # Material costs indicators
        material_keywords = ['material', 'cable', 'pipe', 'joint', 'concrete', 'aggregate', 'sand', 'cement']
        if any(keyword in description for keyword in material_keywords):
            return ExpenseCategory.materials
        
        # Labor costs indicators
        labor_keywords = ['wage', 'salary', 'labor', 'labour', 'staff', 'payroll', 'overtime']
        if any(keyword in description for keyword in labor_keywords):
            return ExpenseCategory.labor
        
        # Plant and machinery indicators
        plant_keywords = ['plant', 'machinery', 'equipment', 'hire', 'rental', 'excavator', 'truck']
        if any(keyword in description for keyword in plant_keywords):
            return ExpenseCategory.plant_machinery
        
        # Subcontractor indicators
        subcontractor_keywords = ['subcontractor', 'sub-contractor', 'contractor', 'outsource']
        if any(keyword in description for keyword in subcontractor_keywords):
            return ExpenseCategory.subcontractors
        
        # Transport indicators
        transport_keywords = ['transport', 'delivery', 'fuel', 'vehicle', 'mileage']
        if any(keyword in description for keyword in transport_keywords):
            return ExpenseCategory.transport
        
        # Default to other if no match found
        return ExpenseCategory.other
    
    def extract_job_code_from_class(self, class_name: str) -> Optional[str]:
        """
        Extract job code from QuickBooks class name
        This is like reading the project number from a file folder label
        """
        if not class_name or pd.isna(class_name) or class_name == 'Not Specified':
            return None
        
        # Convert to string and clean
        class_name = str(class_name).strip()
        
        # Your job codes might be in different formats, adjust as needed
        # Example: "JOB001-Main Road Works" -> "JOB001"
        # Example: "SGN-2024-001" -> "SGN-2024-001"
        
        # Try to find patterns that match your job code structure
        import re
        
        # Pattern 1: JOB followed by numbers
        pattern1 = r'JOB\d+'
        match1 = re.search(pattern1, class_name, re.IGNORECASE)
        if match1:
            return match1.group().upper()
        
        # Pattern 2: SGN followed by year and number
        pattern2 = r'SGN-\d{4}-\d+'
        match2 = re.search(pattern2, class_name, re.IGNORECASE)
        if match2:
            return match2.group().upper()
        
        # Pattern 3: Any combination of letters and numbers with hyphens
        pattern3 = r'[A-Z]{2,}-\d{4}-\d+'
        match3 = re.search(pattern3, class_name, re.IGNORECASE)
        if match3:
            return match3.group().upper()
        
        # If no pattern matches, return the class name as is (you can adjust this)
        return class_name.upper()
    
    def process_pnl_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process the P&L data and extract expenses by job
        This is like going through each line item and sorting it into the right project folder
        """
        processed_count = 0
        skipped_count = 0
        
        try:
            # Find the columns that contain job classes
            # QuickBooks P&L by Class typically has job codes as column headers
            job_columns = []
            for col in df.columns:
                if col and str(col).strip() and str(col).strip() != 'Account' and str(col).strip() != 'Total':
                    job_code = self.extract_job_code_from_class(str(col))
                    if job_code:
                        job_columns.append((col, job_code))
            
            logger.info(f"Found {len(job_columns)} job columns in P&L report")
            
            # Process each row for expenses
            for index, row in df.iterrows():
                try:
                    account_name = row.get('Account', '')
                    if not account_name or pd.isna(account_name):
                        continue
                    
                    account_name = str(account_name).strip()
                    
                    # Skip header rows and total rows
                    if any(skip_word in account_name.lower() for skip_word in ['total', 'income', 'revenue', 'gross profit']):
                        continue
                    
                    # Process each job column
                    for col_name, job_code in job_columns:
                        try:
                            amount = row.get(col_name, 0)
                            if pd.isna(amount) or amount == 0:
                                continue
                            
                            # Ensure amount is positive for expenses
                            amount = abs(float(amount))
                            
                            # Find the corresponding job in database
                            job_id = self.job_mappings.get(job_code)
                            if not job_id:
                                # Try to create job if it doesn't exist
                                job_id = self.create_job_if_not_exists(job_code)
                            
                            if job_id:
                                # Categorize the expense
                                category = self.categorize_expense(account_name)
                                
                                # Create expense record
                                expense_data = {
                                    'job_id': job_id,
                                    'category': category,
                                    'description': account_name,
                                    'amount': amount,
                                    'expense_date': datetime.now().date(),
                                    'source': 'P&L Import'
                                }
                                
                                self.processed_expenses.append(expense_data)
                                processed_count += 1
                                
                        except Exception as e:
                            logger.error(f"Error processing expense for {job_code}: {str(e)}")
                            skipped_count += 1
                            continue
                            
                except Exception as e:
                    logger.error(f"Error processing row {index}: {str(e)}")
                    skipped_count += 1
                    continue
            
            return {
                'processed_count': processed_count,
                'skipped_count': skipped_count,
                'total_expenses': len(self.processed_expenses)
            }
            
        except Exception as e:
            logger.error(f"Error processing P&L data: {str(e)}")
            raise ValueError(f"Failed to process P&L data: {str(e)}")
    
    def create_job_if_not_exists(self, job_code: str) -> Optional[int]:
        """
        Create a new job if it doesn't exist in the database
        This is like adding a new project folder when you encounter a new project
        """
        try:
            from ..models import JobCreate, JobStatus
            
            job_data = JobCreate(
                job_code=job_code,
                job_name=f"Auto-created from P&L: {job_code}",
                client="Unknown",  # You can improve this by parsing client from job code
                status=JobStatus.active,
                contract_value=0.0,
                progress_percentage=0.0
            )
            
            job = crud.create_job(self.db, job_data)
            self.job_mappings[job_code] = job.id
            logger.info(f"Created new job: {job_code} with ID: {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Error creating job {job_code}: {str(e)}")
            return None
    
    def save_expenses_to_database(self) -> int:
        """
        Save all processed expenses to the database
        This is like filing all the sorted expenses into the permanent record system
        """
        saved_count = 0
        
        try:
            for expense_data in self.processed_expenses:
                try:
                    from ..models import ExpenseCreate
                    
                    expense_create = ExpenseCreate(
                        job_id=expense_data['job_id'],
                        category=expense_data['category'],
                        description=expense_data['description'],
                        amount=expense_data['amount'],
                        expense_date=expense_data['expense_date']
                    )
                    
                    expense = crud.create_expense(self.db, expense_create)
                    if expense:
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Error saving expense: {str(e)}")
                    self.errors.append(f"Failed to save expense: {str(e)}")
                    continue
            
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving expenses to database: {str(e)}")
            raise ValueError(f"Failed to save expenses: {str(e)}")

def process_pnl_file(file_path: str, db: Session) -> Dict[str, Any]:
    """
    Main function to process a P&L file
    This is the main coordinator that orchestrates the entire P&L processing workflow
    """
    parser = PnLParser(db)
    
    try:
        # Step 1: Load existing job mappings
        parser.load_job_mappings()
        
        # Step 2: Parse the Excel file
        df = parser.parse_excel_file(file_path)
        
        # Step 3: Process the P&L data
        processing_result = parser.process_pnl_data(df)
        
        # Step 4: Save expenses to database
        saved_count = parser.save_expenses_to_database()
        
        # Step 5: Check for budget alerts after adding new expenses
        for job_id in set(expense['job_id'] for expense in parser.processed_expenses):
            crud.check_and_create_budget_alerts(db, job_id)
        
        return {
            'success': True,
            'expenses_created': saved_count,
            'processing_summary': processing_result,
            'errors': parser.errors,
            'message': f"Successfully processed P&L report. {saved_count} expenses added."
        }
        
    except Exception as e:
        logger.error(f"Error in process_pnl_file: {str(e)}")
        return {
            'success': False,
            'expenses_created': 0,
            'error': str(e),
            'message': f"Failed to process P&L report: {str(e)}"
        }