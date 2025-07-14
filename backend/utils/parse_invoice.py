import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvoiceParser:
    """
    Parser for QuickBooks invoice reports
    Handles A/R Paid and A/R Unpaid invoice data
    """
    
    def __init__(self):
        self.required_columns = [
            'Type', 'Date', 'Num', 'Name', 'Class', 'Amount', 'Balance'
        ]
        self.optional_columns = [
            'A/R Paid', 'Status', 'Terms', 'Due Date', 'Aging'
        ]
    
    def parse_invoice_file(self, file_path: str) -> Dict:
        """
        Parse invoice Excel file and extract relevant data
        
        Args:
            file_path: Path to the invoice Excel file
            
        Returns:
            Dictionary containing parsed invoice data
        """
        try:
            logger.info(f"📊 Starting invoice file parsing: {file_path}")
            
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)
            
            # Log basic info
            logger.info(f"📋 Invoice file shape: {df.shape}")
            logger.info(f"📋 Available columns: {list(df.columns)}")
            
            # Clean and validate data
            df = self._clean_dataframe(df)
            
            # Process invoice data
            invoice_data = self._process_invoice_data(df)
            
            # Generate summary
            summary = self._generate_summary(invoice_data)
            
            result = {
                'success': True,
                'data': invoice_data,
                'summary': summary,
                'processed_at': datetime.now().isoformat(),
                'file_path': file_path
            }
            
            logger.info(f"✅ Invoice parsing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error parsing invoice file: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {},
                'summary': {},
                'processed_at': datetime.now().isoformat()
            }
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the dataframe"""
        
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Convert date columns
        date_columns = ['Date', 'Due Date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert amount columns to numeric
        amount_columns = ['Amount', 'Balance', 'A/R Paid']
        for col in amount_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Fill NaN values
        df = df.fillna({
            'Class': 'UNASSIGNED',
            'Name': 'UNKNOWN',
            'Amount': 0,
            'Balance': 0,
            'A/R Paid': 0
        })
        
        # Clean job codes (Class column)
        if 'Class' in df.columns:
            df['Class'] = df['Class'].astype(str).str.strip().str.upper()
        
        return df
    
    def _process_invoice_data(self, df: pd.DataFrame) -> Dict:
        """Process invoice data and organize by job codes"""
        
        invoice_data = {}
        
        # Group by job code (Class)
        for job_code, job_df in df.groupby('Class'):
            if job_code == 'UNASSIGNED':
                continue
                
            # Calculate totals for this job
            total_invoiced = job_df['Amount'].sum()
            total_paid = job_df['A/R Paid'].sum() if 'A/R Paid' in job_df.columns else 0
            outstanding_balance = job_df['Balance'].sum()
            
            # Categorize invoices
            paid_invoices = job_df[job_df['Balance'] <= 0] if 'Balance' in job_df.columns else pd.DataFrame()
            unpaid_invoices = job_df[job_df['Balance'] > 0] if 'Balance' in job_df.columns else pd.DataFrame()
            
            # Process individual invoices
            invoices_list = []
            for _, row in job_df.iterrows():
                invoice_info = {
                    'invoice_number': str(row.get('Num', '')),
                    'date': row.get('Date').strftime('%Y-%m-%d') if pd.notna(row.get('Date')) else None,
                    'client_name': str(row.get('Name', '')),
                    'amount': float(row.get('Amount', 0)),
                    'balance': float(row.get('Balance', 0)),
                    'paid_amount': float(row.get('A/R Paid', 0)),
                    'status': 'PAID' if row.get('Balance', 0) <= 0 else 'UNPAID',
                    'due_date': row.get('Due Date').strftime('%Y-%m-%d') if pd.notna(row.get('Due Date')) else None,
                    'aging_days': self._calculate_aging(row.get('Due Date')) if pd.notna(row.get('Due Date')) else 0
                }
                invoices_list.append(invoice_info)
            
            # Store job data
            invoice_data[job_code] = {
                'job_code': job_code,
                'total_invoiced': float(total_invoiced),
                'total_paid': float(total_paid),
                'outstanding_balance': float(outstanding_balance),
                'paid_invoices_count': len(paid_invoices),
                'unpaid_invoices_count': len(unpaid_invoices),
                'invoices': invoices_list,
                'payment_rate': (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
            }
        
        return invoice_data
    
    def _calculate_aging(self, due_date) -> int:
        """Calculate aging days from due date"""
        if pd.isna(due_date):
            return 0
        
        today = datetime.now().date()
        if isinstance(due_date, str):
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        elif hasattr(due_date, 'date'):
            due_date = due_date.date()
        
        return (today - due_date).days
    
    def _generate_summary(self, invoice_data: Dict) -> Dict:
        """Generate summary statistics"""
        
        total_invoiced = sum(job['total_invoiced'] for job in invoice_data.values())
        total_paid = sum(job['total_paid'] for job in invoice_data.values())
        total_outstanding = sum(job['outstanding_balance'] for job in invoice_data.values())
        
        paid_invoices_count = sum(job['paid_invoices_count'] for job in invoice_data.values())
        unpaid_invoices_count = sum(job['unpaid_invoices_count'] for job in invoice_data.values())
        
        # Job performance analysis
        job_performance = []
        for job_code, job_data in invoice_data.items():
            performance = {
                'job_code': job_code,
                'total_invoiced': job_data['total_invoiced'],
                'payment_rate': job_data['payment_rate'],
                'outstanding_balance': job_data['outstanding_balance'],
                'status': 'HEALTHY' if job_data['payment_rate'] > 80 else 'ATTENTION_NEEDED'
            }
            job_performance.append(performance)
        
        # Sort by outstanding balance
        job_performance.sort(key=lambda x: x['outstanding_balance'], reverse=True)
        
        return {
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
            'overall_payment_rate': (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0,
            'paid_invoices_count': paid_invoices_count,
            'unpaid_invoices_count': unpaid_invoices_count,
            'total_jobs': len(invoice_data),
            'job_performance': job_performance[:10],  # Top 10 jobs by outstanding balance
            'alerts': self._generate_alerts(invoice_data)
        }
    
    def _generate_alerts(self, invoice_data: Dict) -> List[Dict]:
        """Generate alerts for overdue invoices and payment issues"""
        
        alerts = []
        
        for job_code, job_data in invoice_data.items():
            # Check for low payment rates
            if job_data['payment_rate'] < 50:
                alerts.append({
                    'type': 'LOW_PAYMENT_RATE',
                    'job_code': job_code,
                    'message': f"Job {job_code} has low payment rate: {job_data['payment_rate']:.1f}%",
                    'severity': 'HIGH',
                    'value': job_data['payment_rate']
                })
            
            # Check for high outstanding balances
            if job_data['outstanding_balance'] > 10000:  # Configurable threshold
                alerts.append({
                    'type': 'HIGH_OUTSTANDING_BALANCE',
                    'job_code': job_code,
                    'message': f"Job {job_code} has high outstanding balance: £{job_data['outstanding_balance']:,.2f}",
                    'severity': 'MEDIUM',
                    'value': job_data['outstanding_balance']
                })
            
            # Check for overdue invoices
            overdue_invoices = [inv for inv in job_data['invoices'] 
                              if inv['status'] == 'UNPAID' and inv['aging_days'] > 30]
            
            if overdue_invoices:
                alerts.append({
                    'type': 'OVERDUE_INVOICES',
                    'job_code': job_code,
                    'message': f"Job {job_code} has {len(overdue_invoices)} overdue invoices",
                    'severity': 'HIGH',
                    'value': len(overdue_invoices)
                })
        
        return alerts

# Utility functions for external use
def parse_invoice_report(file_path: str) -> Dict:
    """
    Main function to parse invoice report
    
    Args:
        file_path: Path to the invoice Excel file
        
    Returns:
        Dictionary containing parsed invoice data
    """
    parser = InvoiceParser()
    return parser.parse_invoice_file(file_path)

def get_job_invoice_summary(file_path: str, job_code: str) -> Optional[Dict]:
    """
    Get invoice summary for a specific job
    
    Args:
        file_path: Path to the invoice Excel file
        job_code: Job code to get summary for
        
    Returns:
        Dictionary containing job invoice summary or None if not found
    """
    result = parse_invoice_report(file_path)
    
    if result['success'] and job_code in result['data']:
        return result['data'][job_code]
    
    return None

def get_overdue_invoices(file_path: str, days_threshold: int = 30) -> List[Dict]:
    """
    Get all overdue invoices across all jobs
    
    Args:
        file_path: Path to the invoice Excel file
        days_threshold: Number of days to consider as overdue
        
    Returns:
        List of overdue invoice dictionaries
    """
    result = parse_invoice_report(file_path)
    overdue_invoices = []
    
    if result['success']:
        for job_code, job_data in result['data'].items():
            for invoice in job_data['invoices']:
                if invoice['status'] == 'UNPAID' and invoice['aging_days'] > days_threshold:
                    invoice['job_code'] = job_code
                    overdue_invoices.append(invoice)
    
    return overdue_invoices

# Example usage and testing
if __name__ == "__main__":
    # Test the parser
    test_file = "test_invoice_report.xlsx"
    
    try:
        result = parse_invoice_report(test_file)
        
        if result['success']:
            print("✅ Invoice parsing successful!")
            print(f"📊 Summary: {result['summary']}")
            
            # Print job details
            for job_code, job_data in result['data'].items():
                print(f"\n💼 Job: {job_code}")
                print(f"   Total Invoiced: £{job_data['total_invoiced']:,.2f}")
                print(f"   Total Paid: £{job_data['total_paid']:,.2f}")
                print(f"   Outstanding: £{job_data['outstanding_balance']:,.2f}")
                print(f"   Payment Rate: {job_data['payment_rate']:.1f}%")
        else:
            print(f"❌ Error: {result['error']}")
            
    except FileNotFoundError:
        print(f"⚠️  Test file {test_file} not found. Parser code is ready for use.")