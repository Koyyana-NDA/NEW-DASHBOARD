import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from backend.database import get_db_connection
from backend.crud import get_job_by_code, get_expenses_by_job, get_budgets_by_job

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BudgetAlertSystem:
    """
    Budget monitoring and alert system
    Checks budgets against actual costs and sends alerts
    """
    
    def __init__(self, alert_config_path: str = "backend/config/alert_config.json"):
        self.alert_config_path = alert_config_path
        self.alert_config = {}
        self.load_alert_config()
        
    def load_alert_config(self):
        """Load alert configuration"""
        try:
            if os.path.exists(self.alert_config_path):
                with open(self.alert_config_path, 'r') as f:
                    self.alert_config = json.load(f)
                logger.info(f"📋 Loaded alert config from {self.alert_config_path}")
            else:
                self.create_default_alert_config()
        except Exception as e:
            logger.error(f"❌ Error loading alert config: {str(e)}")
            self.create_default_alert_config()
    
    def create_default_alert_config(self):
        """Create default alert configuration"""
        default_config = {
            "alert_thresholds": {
                "warning": 0.8,  # 80% of budget
                "critical": 0.95,  # 95% of budget
                "exceeded": 1.0   # 100% of budget
            },
            "email_settings": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipients": ["john@nda.com", "admin@nda.com"]
            },
            "alert_frequency": {
                "warning": "daily",
                "critical": "immediate",
                "exceeded": "immediate"
            },
            "categories": {
                "material": "Material & Supplies",
                "labour": "Labour & Wages",
                "plant": "Plant & Equipment",
                "subcontract": "Subcontract Costs",
                "overheads": "Overheads"
            }
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.alert_config_path), exist_ok=True)
        
        with open(self.alert_config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        self.alert_config = default_config
        logger.info(f"📋 Created default alert config: {self.alert_config_path}")
    
    def check_job_budgets(self, job_code: str) -> Dict:
        """
        Check budgets for a specific job
        
        Args:
            job_code: Job code to check
            
        Returns:
            Dictionary with budget check results
        """
        try:
            logger.info(f"🔍 Checking budgets for job {job_code}")
            
            # Get database connection
            db = next(get_db_connection())

            # Resolve job code → internal ID
            job = get_job_by_code(db, job_code)
            if not job:
                return {'success': False, 'error': f'Job {job_code} not found'}
            job_id = job.id
            
            # Get job expenses and budgets
            expenses = get_expenses_by_job(db, job_id)
            budgets = get_budgets_by_job(db, job_id)
            
            if not budgets:
                logger.warning(f"⚠️  No budgets found for job {job_code}")
                return {'success': False, 'error': f'No budgets found for job {job_code}'}
            
            # Calculate expense totals by category
            expense_totals = self._calculate_expense_totals(expenses)
            
            # Check each budget category
            alerts = []
            budget_status = {}
            
            for budget in budgets:
                category = budget.category
                budget_amount = budget.amount
                actual_amount = expense_totals.get(category, 0)
                
                # Calculate percentage used
                percentage_used = (actual_amount / budget_amount) if budget_amount > 0 else 0
                
                # Determine alert level
                alert_level = self._get_alert_level(percentage_used)
                
                budget_status[category] = {
                    'budget_amount': budget_amount,
                    'actual_amount': actual_amount,
                    'percentage_used': percentage_used * 100,
                    'remaining_budget': budget_amount - actual_amount,
                    'alert_level': alert_level,
                    'over_budget': actual_amount > budget_amount
                }
                
                # Create alert if threshold exceeded
                if alert_level != 'normal':
                    alerts.append({
                        'job_code': job_code,
                        'category': category,
                        'alert_level': alert_level,
                        'budget_amount': budget_amount,
                        'actual_amount': actual_amount,
                        'percentage_used': percentage_used * 100,
                        'over_budget': actual_amount > budget_amount,
                        'timestamp': datetime.now().isoformat()
                    })
            
            result = {
                'success': True,
                'job_code': job_code,
                'budget_status': budget_status,
                'alerts': alerts,
                'total_alerts': len(alerts),
                'checked_at': datetime.now().isoformat()
            }
            
            # Send alerts if any
            if alerts:
                self._send_alerts(alerts)
            
            logger.info(f"✅ Budget check completed for job {job_code}. {len(alerts)} alerts generated")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error checking budgets for job {job_code}: {str(e)}")
            return {'success': False, 'error': f'Error checking budgets: {str(e)}'}
    
    def check_all_jobs_budgets(self) -> Dict:
        """
        Check budgets for all jobs
        
        Returns:
            Dictionary with budget check results for all jobs
        """
        try:
            logger.info("🔍 Checking budgets for all jobs")
            
            # Get database connection
            db = next(get_db_connection())
            
            # Get all jobs with budgets
            from backend.crud import get_all_jobs
            jobs = get_all_jobs(db)
            
            all_results = {}
            total_alerts = 0
            
            for job in jobs:
                job_result = self.check_job_budgets(job.job_code)
                if job_result['success']:
                    all_results[job.job_code] = job_result
                    total_alerts += job_result['total_alerts']
            
            summary = {
                'success': True,
                'total_jobs_checked': len(all_results),
                'total_alerts': total_alerts,
                'checked_at': datetime.now().isoformat(),
                'job_results': all_results
            }
            
            logger.info(f"✅ All jobs budget check completed. {total_alerts} total alerts")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error checking all jobs budgets: {str(e)}")
            return {'success': False, 'error': f'Error checking all jobs budgets: {str(e)}'}
    
    def _calculate_expense_totals(self, expenses: List) -> Dict[str, float]:
        """Calculate total expenses by category"""
        totals = {}
        
        for expense in expenses:
            category = expense.category
            amount = expense.amount
            
            if category not in totals:
                totals[category] = 0
            totals[category] += amount
        
        return totals
    
    def _get_alert_level(self, percentage_used: float) -> str:
        """Determine alert level based on percentage used"""
        thresholds = self.alert_config.get('alert_thresholds', {})
        
        if percentage_used >= thresholds.get('exceeded', 1.0):
            return 'exceeded'
        elif percentage_used >= thresholds.get('critical', 0.95):
            return 'critical'
        elif percentage_used >= thresholds.get('warning', 0.8):
            return 'warning'
        else:
            return 'normal'
    
    def _send_alerts(self, alerts: List[Dict]):
        """Send alert notifications"""
        try:
            email_settings = self.alert_config.get('email_settings', {})
            
            if not email_settings.get('sender_email') or not email_settings.get('sender_password'):
                logger.warning("⚠️  Email settings not configured, skipping email alerts")
                return
            
            # Group alerts by job and level
            grouped_alerts = {}
            for alert in alerts:
                job_code = alert['job_code']
                level = alert['alert_level']
                
                if job_code not in grouped_alerts:
                    grouped_alerts[job_code] = {}
                if level not in grouped_alerts[job_code]:
                    grouped_alerts[job_code][level] = []
                
                grouped_alerts[job_code][level].append(alert)
            
            # Send email for each job with alerts
            for job_code, job_alerts in grouped_alerts.items():
                self._send_job_alert_email(job_code, job_alerts)
            
            logger.info(f"📧 Alert emails sent for {len(grouped_alerts)} jobs")
            
        except Exception as e:
            logger.error(f"❌ Error sending alerts: {str(e)}")
    
    def _send_job_alert_email(self, job_code: str, job_alerts: Dict):
        """Send alert email for a specific job"""
        try:
            email_settings = self.alert_config.get('email_settings', {})
            
            # Create email content
            subject = f"Budget Alert - Job {job_code}"
            body = self._create_alert_email_body(job_code, job_alerts)
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = email_settings['sender_email']
            msg['To'] = ', '.join(email_settings['recipients'])
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port'])
            server.starttls()
            server.login(email_settings['sender_email'], email_settings['sender_password'])
            
            text = msg.as_string()
            server.sendmail(email_settings['sender_email'], email_settings['recipients'], text)
            server.quit()
            
            logger.info(f"📧 Alert email sent for job {job_code}")
            
        except Exception as e:
            logger.error(f"❌ Error sending email for job {job_code}: {str(e)}")
    
    def _create_alert_email_body(self, job_code: str, job_alerts: Dict) -> str:
        """Create HTML email body for alerts"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert-header {{ color: #d32f2f; font-size: 18px; font-weight: bold; }}
                .job-header {{ color: #1976d2; font-size: 16px; font-weight: bold; margin-top: 20px; }}
                .alert-critical {{ background-color: #ffebee; border-left: 4px solid #d32f2f; padding: 10px; margin: 10px 0; }}
                .alert-warning {{ background-color: #fff3e0; border-left: 4px solid #f57c00; padding: 10px; margin: 10px 0; }}
                .alert-exceeded {{ background-color: #f3e5f5; border-left: 4px solid #7b1fa2; padding: 10px; margin: 10px 0; }}
                .alert-details {{ margin-left: 20px; }}
            </style>
        </head>
        <body>
            <div class="alert-header">🚨 Budget Alert - Job {job_code}</div>
            <p>The following budget categories have exceeded their thresholds:</p>
        """
        
        for level, alerts in job_alerts.items():
            html += f'<div class="alert-{level}">'
            html += f'<strong>{level.upper()} ALERTS:</strong><br>'
            
            for alert in alerts:
                html += f"""
                <div class="alert-details">
                    <strong>Category:</strong> {alert['category']}<br>
                    <strong>Budget:</strong> £{alert['budget_amount']:,.2f}<br>
                    <strong>Actual:</strong> £{alert['actual_amount']:,.2f}<br>
                    <strong>Percentage Used:</strong> {alert['percentage_used']:.1f}%<br>
                    <strong>Over Budget:</strong> {'Yes' if alert['over_budget'] else 'No'}<br>
                </div>
                """
            
            html += '</div>'
        
        html += """
            <p>Please review and take appropriate action.</p>
            <p>This alert was generated automatically by the NDA Budget Monitoring System.</p>
        </body>
        </html>
        """
        
        return html
    
    def update_alert_config(self, new_config: Dict):
        """Update alert configuration"""
        try:
            # Merge with existing config
            for key, value in new_config.items():
                if key in self.alert_config:
                    if isinstance(value, dict) and isinstance(self.alert_config[key], dict):
                        self.alert_config[key].update(value)
                    else:
                        self.alert_config[key] = value
                else:
                    self.alert_config[key] = value
            
            # Save updated config
            with open(self.alert_config_path, 'w') as f:
                json.dump(self.alert_config, f, indent=2)
            
            logger.info("✅ Alert configuration updated")
            return {'success': True, 'message': 'Alert configuration updated successfully'}
            
        except Exception as e:
            logger.error(f"❌ Error updating alert config: {str(e)}")
            return {'success': False, 'error': f'Error updating alert config: {str(e)}'}

# Utility functions for easy access
def check_job_budget(job_code: str) -> Dict:
    """Quick function to check budget for a job"""
    alert_system = BudgetAlertSystem()
    return alert_system.check_job_budgets(job_code)

def check_all_budgets() -> Dict:
    """Quick function to check budgets for all jobs"""
    alert_system = BudgetAlertSystem()
    return alert_system.check_all_jobs_budgets()

def setup_budget_alerts(email_config: Dict = None) -> Dict:
    """Setup budget alert system with email configuration"""
    alert_system = BudgetAlertSystem()
    
    if email_config:
        return alert_system.update_alert_config({'email_settings': email_config})
    
    return {'success': True, 'message': 'Budget alert system initialized'}