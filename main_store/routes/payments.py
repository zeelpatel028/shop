from flask import render_template, request
from .. import main_store_bp
from database.db import supabase
from datetime import datetime, timedelta

def safe_float(value, default=0.0):
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

@main_store_bp.route('/payments')
def payments():
    period = request.args.get('period', 'all')
    try:
        now = datetime.now()
        
        # Only fetch payments linked to the Main Store
        query = supabase.table('payments').select('*, bills(bill_no)').eq('store_name', 'Main Store').order('created_at', desc=True)
        
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
        elif period == 'week':
            start_date = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
        elif period == 'year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
            
        payments_response = query.execute()
        payments_list = payments_response.data or []
        
        # Calculate summaries
        cash_payments = [p for p in payments_list if p.get('payment_method') == 'Cash']
        upi_payments = [p for p in payments_list if p.get('payment_method') == 'UPI']
        
        cash_total = sum(safe_float(p.get('paid_amount')) for p in cash_payments)
        upi_total = sum(safe_float(p.get('paid_amount')) for p in upi_payments)
        
        cash_count = len(cash_payments)
        upi_count = len(upi_payments)
        
    except Exception as e:
        print(f"Error fetching payment data: {e}")
        payments_list = []
        cash_total = 0
        upi_total = 0
        cash_count = 0
        upi_count = 0
        
    return render_template('payments_main.html', 
                         payments=payments_list, 
                         cash_total=cash_total, 
                         upi_total=upi_total,
                         cash_count=cash_count,
                         upi_count=upi_count,
                         active_period=period)
