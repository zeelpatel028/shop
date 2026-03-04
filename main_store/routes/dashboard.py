from flask import render_template, redirect, url_for, request, jsonify, flash
from .. import main_store_bp
from database.db import supabase
from datetime import datetime
from collections import Counter, defaultdict

def safe_float(value, default=0.0):
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    try:
        if not value: return default
        return int(float(str(value)))
    except (ValueError, TypeError):
        return default

@main_store_bp.route('/')
def index():
    try:
        # Filter products by store_name = 'Main Store'
        prods_res = supabase.table('products').select('*').eq('store_name', 'Main Store').execute()
        all_products = prods_res.data or []
        product_count = len(all_products)
        
        # Filter bills by store_name = 'Main Store'
        bills_res = supabase.table('bills').select('*').eq('store_name', 'Main Store').order('created_at', desc=True).execute()
        all_bills = bills_res.data or []
        paid_bills = [b for b in all_bills if b.get('payment_status') == 'Paid']
        bill_count = len(paid_bills)
        
        total_revenue = sum(safe_float(bill.get('bill_total')) for bill in paid_bills)
        
        # Calculate Profit
        items_res = supabase.table('bill_items').select('product_id, product_name, quantity, bill_id, profit_margin').execute()
        bill_items = items_res.data or []
        
        product_profits = {p['product_id']: safe_float(p.get('profit_margin')) for p in all_products}
        
        total_profit = 0
        product_sales = Counter()
        main_paid_bill_ids = {b.get('bill_id') for b in paid_bills if b.get('bill_id')}
        
        for item in bill_items:
            # We need to make sure the item belongs to a Paid Main Store bill
            if item.get('bill_id') in main_paid_bill_ids:
                p_id = item.get('product_id')
                qty = safe_float(item.get('quantity'))
                
                item_profit_margin = item.get('profit_margin')
                margin = safe_float(item_profit_margin) if item_profit_margin is not None else product_profits.get(p_id, 0)
                total_profit += (qty * margin) if item_profit_margin is None else margin
                
                product_sales[item.get('product_name', 'Unknown')] += qty

        avg_order = total_revenue / bill_count if bill_count else 0
        
        # Today's stats
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        today_bills = [b for b in paid_bills if (b.get('created_at') or '') >= today_start]
        today_revenue = sum(safe_float(b.get('bill_total')) for b in today_bills)
        today_count = len(today_bills)
        
        recent_bills = all_bills[:5] # keep all bills for activity feed
        top_products = product_sales.most_common(5)
        low_stock = [p for p in all_products if safe_float(p.get('stock')) <= 10.0]
        profit_pct = (total_profit / total_revenue * 100) if total_revenue else 0

    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        product_count = bill_count = total_revenue = total_profit = avg_order = today_revenue = today_count = profit_pct = 0
        recent_bills = []
        top_products = []
        low_stock = []

    return render_template('main_store.html', 
                         product_count=product_count, 
                         bill_count=bill_count, 
                         revenue=total_revenue,
                         total_profit=total_profit,
                         avg_order=avg_order,
                         today_revenue=today_revenue,
                         today_count=today_count,
                         recent_bills=recent_bills,
                         top_products=top_products,
                         low_stock=low_stock,
                         profit_pct=profit_pct)

@main_store_bp.route('/credit-customer')
def credit_customer():
    return redirect(url_for('customer.dashboard'))

@main_store_bp.route('/seller')
def seller():
    return redirect(url_for('seller.index'))

@main_store_bp.route('/employee')
def employee():
    return redirect(url_for('employee.index'))
