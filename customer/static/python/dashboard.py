from flask import render_template
from ... import customer_bp
from database.db import supabase

@customer_bp.route('/')
def dashboard():
    try:
        # Total Customers
        res_cust = supabase.table('customer').select('id', count='exact').execute()
        total_customers = res_cust.count or 0
        
        # Pending Bills (Unpaid)
        res_pending = supabase.table('credit_bill').select('id', count='exact').neq('payment_status', 'Paid').execute()
        pending_bills_count = res_pending.count or 0
        
        # Approved Bills (Paid)
        res_paid = supabase.table('credit_bill').select('id', count='exact').eq('payment_status', 'Paid').execute()
        paid_bills_count = res_paid.count or 0

        stats = {
            'total_customers': total_customers,
            'pending_bills': pending_bills_count,
            'paid_bills': paid_bills_count
        }
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        stats = {'total_customers': 0, 'pending_bills': 0, 'paid_bills': 0}
        
    return render_template('dashboard.html', stats=stats)
