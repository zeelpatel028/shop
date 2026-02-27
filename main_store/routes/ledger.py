from flask import render_template, request
from .. import main_store_bp
from database.db import supabase
from datetime import datetime, timedelta
from collections import defaultdict

def safe_float(value, default=0.0):
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

@main_store_bp.route('/ledger')
def ledger():
    period = request.args.get('period', 'all')
    try:
        now = datetime.now()
        
        query = supabase.table('bills').select('*').eq('store_name', 'Main Store').order('created_at', desc=True)
        
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
            
        bills_response = query.execute()
        bills = bills_response.data or []
        
        all_items_res = supabase.table('bill_items').select('bill_id, product_id, quantity').execute()
        all_items = all_items_res.data or []
        
        prods_res = supabase.table('products').select('product_id, profit_margin').execute()
        product_profits = {p['product_id']: safe_float(p.get('profit_margin')) for p in prods_res.data} if prods_res.data else {}
        
        items_by_bill = defaultdict(list)
        for item in all_items:
            items_by_bill[item['bill_id']].append(item)
            
        total_revenue = 0
        total_profit = 0
        for b in bills:
            b_id = b.get('bill_id')
            b_profit = 0
            for item in items_by_bill.get(b_id, []):
                p_id = item.get('product_id')
                qty = safe_float(item.get('quantity'))
                margin = product_profits.get(p_id, 0)
                b_profit += (qty * margin)
            
            b['bill_profit'] = b_profit
            total_revenue += safe_float(b.get('bill_total'))
            total_profit += b_profit
            
        total_bills = len(bills)
        
        graph_labels = []
        graph_data = []
        
        sorted_bills = sorted(bills, key=lambda x: x.get('created_at'))
        
        def get_group_key(created_at, period):
            dt = datetime.fromisoformat(created_at[:19])
            if period == 'day': return dt.strftime('%H:00')
            if period == 'week': return dt.strftime('%a')
            if period == 'month': return dt.strftime('%d %b')
            if period == 'year': return dt.strftime('%B')
            return dt.strftime('%Y-%m-%d')

        trend_map = defaultdict(float)
        for b in sorted_bills:
            key = get_group_key(b.get('created_at'), period)
            trend_map[key] += safe_float(b.get('bill_total'))
        
        if period == 'all':
            graph_labels = sorted(trend_map.keys())
        elif period == 'day':
            graph_labels = [f"{h:02d}:00" for h in range(24)]
        elif period == 'week':
            graph_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        elif period == 'month':
            from calendar import monthrange
            days_in_month = monthrange(now.year, now.month)[1]
            graph_labels = [f"{d:02d} {now.strftime('%b')}" for d in range(1, days_in_month + 1)]
        elif period == 'year':
            graph_labels = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        else:
            graph_labels = sorted(trend_map.keys())

        graph_data = [trend_map.get(label, 0) for label in graph_labels]
        
    except Exception as e:
        print(f"Error fetching ledger: {e}")
        bills = []
        total_revenue = 0
        total_bills = 0
        total_profit = 0
        graph_labels = []
        graph_data = []
        
    return render_template('ledger_main.html', 
                         bills=bills, 
                         total_revenue=total_revenue, 
                         total_bills=total_bills,
                         total_profit=total_profit,
                         active_period=period,
                         graph_labels=graph_labels,
                         graph_data=graph_data)
