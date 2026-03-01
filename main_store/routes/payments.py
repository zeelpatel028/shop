from flask import render_template, request, jsonify
from .. import main_store_bp
from database.db import supabase
from datetime import datetime, timedelta
from ..utils.payment_service import PaymentService
import uuid

def safe_float(value, default=0.0):
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

@main_store_bp.route('/payments')
def payments():
    period = request.args.get('period', 'all')
    try:
        from datetime import timezone
        IST = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(IST)
        
        # Only fetch payments linked to the Main Store
        query = supabase.table('payments').select('*, bills!bill_id(bill_no)').eq('store_name', 'Main Store').order('created_at', desc=True)
        
        if period == 'day':
            start_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
            start_utc = start_ist.astimezone(timezone.utc).isoformat()
            query = query.gte('created_at', start_utc)
        elif period == 'week':
            start_ist = (now_ist - timedelta(days=now_ist.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            start_utc = start_ist.astimezone(timezone.utc).isoformat()
            query = query.gte('created_at', start_utc)
        elif period == 'month':
            start_ist = now_ist.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_utc = start_ist.astimezone(timezone.utc).isoformat()
            query = query.gte('created_at', start_utc)
        elif period == 'year':
            start_ist = now_ist.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            start_utc = start_ist.astimezone(timezone.utc).isoformat()
            query = query.gte('created_at', start_utc)
            
        payments_response = query.execute()
        standard_payments = payments_response.data or []
        
        # --- FETCH APPROVED CREDIT BILLS AS PAYMENTS ---
        credit_query = supabase.table('credit_bill').select('*').eq('payment_status', 'Paid')
        
        if period == 'day':
            credit_query = credit_query.gte('created_at', start_utc)
        elif period == 'week':
            credit_query = credit_query.gte('created_at', start_utc)
        elif period == 'month':
            credit_query = credit_query.gte('created_at', start_utc)
        elif period == 'year':
            credit_query = credit_query.gte('created_at', start_utc)
            
        credit_res = credit_query.execute()
        credit_payments_raw = credit_res.data or []
        
        # Normalize Credit Bills to match Standard Payments structure
        normalized_credit_payments = []
        for cb in credit_payments_raw:
            # Skip if linked to a standard bill (to avoid double counting)
            if cb.get('bill_id'):
                continue
                
            normalized_credit_payments.append({
                'payment_id': f"CR-{cb.get('id')}", 
                'bill_id': cb.get('id'), 
                'paid_amount': cb.get('total_price'),
                'payment_method': 'Credit Paid',
                'payment_status': 'Paid',
                'created_at': cb.get('created_at'),
                'bills': {'bill_no': f"CR-{cb.get('id')}"} # Mocking the joined object
            })
            
        payments_list = standard_payments + normalized_credit_payments
        payments_list = sorted(payments_list, key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Calculate summaries ONLY for Paid payments
        cash_payments = [p for p in payments_list if p.get('payment_method') == 'Cash' and p.get('payment_status') == 'Paid']
        upi_payments = [p for p in payments_list if p.get('payment_method') == 'UPI' and p.get('payment_status') == 'Paid']
        
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

@main_store_bp.route('/api/check-payment-status/<payment_ref>')
def check_payment_status(payment_ref):
    status = PaymentService.check_status(supabase, payment_ref)
    return jsonify({'status': status})

@main_store_bp.route('/api/verify-upi-payment/<payment_ref>', methods=['POST'])
def verify_upi_payment(payment_ref):
    try:
        success = PaymentService.mark_as_paid(supabase, payment_ref, f"MAN-{uuid.uuid4().hex[:10].upper()}")
        return jsonify({'success': success, 'message': 'Payment confirmed successfully' if success else 'Reference not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Server error: {str(e)}"})
