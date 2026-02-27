from flask import render_template
from ... import customer_bp
from database.db import supabase

@customer_bp.route('/pending-bills')
def pending_bills():
    try:
        # Fetch all unpaid credit bills
        res = supabase.table('credit_bill').select('*, customer:c_id(*)').neq('payment_status', 'Paid').execute()
        raw_bills = res.data or []
        
        # Group by customer
        pending_data = {}
        for bill in raw_bills:
            c_id = bill['c_id']
            if c_id not in pending_data:
                cust = bill.get('customer', {})
                pending_data[c_id] = {
                    'customer_id': c_id,
                    'name': cust.get('name', 'Unknown'),
                    'phone': cust.get('phone_no', '-'),
                    'unpaid_amount': 0,
                    'bill_count': 0
                }
            pending_data[c_id]['unpaid_amount'] += float(bill.get('remaining_amount', 0))
            pending_data[c_id]['bill_count'] += 1
            
        customers_pending = list(pending_data.values())
        
        # Summary stats for the view
        stats = {
            'total_pending_amount': sum(c['unpaid_amount'] for c in customers_pending),
            'total_pending_bills': sum(c['bill_count'] for c in customers_pending)
        }
    except Exception as e:
        print(f"Error fetching pending bills: {e}")
        customers_pending = []
        stats = {'total_pending_amount': 0, 'total_pending_bills': 0}
        
    return render_template('pending_bills.html', customers=customers_pending, stats=stats)

@customer_bp.route('/api/unpaid-bills/<int:c_id>')
def get_customer_unpaid_bills(c_id):
    try:
        res = supabase.table('credit_bill').select('*').eq('c_id', c_id).neq('payment_status', 'Paid').execute()
        return {"status": "success", "bills": res.data or []}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@customer_bp.route('/approve-bills')
def approve_bills():
    try:
        # Fetch all paid credit bills
        res = supabase.table('credit_bill').select('*, customer:c_id(*)').eq('payment_status', 'Paid').execute()
        raw_bills = res.data or []
        
        # Group by customer
        approved_data = {}
        for bill in raw_bills:
            c_id = bill['c_id']
            if c_id not in approved_data:
                cust = bill.get('customer', {})
                approved_data[c_id] = {
                    'customer_id': c_id,
                    'name': cust.get('name', 'Unknown'),
                    'phone': cust.get('phone_no', '-'),
                    'total_paid': 0,
                    'bill_count': 0
                }
            approved_data[c_id]['total_paid'] += float(bill.get('paid_amount', 0))
            approved_data[c_id]['bill_count'] += 1
            
        customers_approved = list(approved_data.values())
        
        # Summary stats for the view
        stats = {
            'total_approved_amount': sum(c['total_paid'] for c in customers_approved),
            'total_approved_bills': sum(c['bill_count'] for c in customers_approved)
        }
    except Exception as e:
        print(f"Error fetching approved bills: {e}")
        customers_approved = []
        stats = {'total_approved_amount': 0, 'total_approved_bills': 0}
        
    return render_template('approve_bills.html', customers=customers_approved, stats=stats)

@customer_bp.route('/api/paid-bills/<int:c_id>')
def get_customer_paid_bills(c_id):
    try:
        res = supabase.table('credit_bill').select('*').eq('c_id', c_id).eq('payment_status', 'Paid').execute()
        return {"status": "success", "bills": res.data or []}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
