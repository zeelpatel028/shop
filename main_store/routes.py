from flask import render_template, redirect, url_for, request, jsonify, flash
from . import main_store_bp
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
        bill_count = len(all_bills)
        
        total_revenue = sum(safe_float(bill.get('bill_total')) for bill in all_bills)
        
        # Calculate Profit
        items_res = supabase.table('bill_items').select('product_id, product_name, quantity').execute()
        bill_items = items_res.data or []
        
        product_profits = {p['product_id']: safe_float(p.get('profit_margin')) for p in all_products}
        
        total_profit = 0
        product_sales = Counter()
        for item in bill_items:
            # We need to make sure the item belongs to a Main Store bill
            # This is a bit complex with standard joins, but we can filter by bill_id in all_bills
            main_bill_ids = {b['bill_id'] for b in all_bills}
            if item.get('bill_id') in main_bill_ids or not item.get('bill_id'): # Fallback for legacy
                p_id = item.get('product_id')
                qty = safe_float(item.get('quantity'))
                margin = product_profits.get(p_id, 0)
                total_profit += (qty * margin)
                product_sales[item.get('product_name', 'Unknown')] += qty

        avg_order = total_revenue / bill_count if bill_count else 0
        
        # Today's stats
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        today_bills = [b for b in all_bills if (b.get('created_at') or '') >= today_start]
        today_revenue = sum(safe_float(b.get('bill_total')) for b in today_bills)
        today_count = len(today_bills)
        
        recent_bills = all_bills[:5]
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

@main_store_bp.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'GET':
        return render_template('add_product_main.html')
    
    try:
        data = request.form
        base_price = safe_float(data.get('base_price'))
        tax_percent = safe_float(data.get('tax_percent'))
        cost_price = safe_float(data.get('cost_price'))
        sell_price = safe_float(data.get('sell_price'))
        tax_amount = (base_price * tax_percent) / 100
        
        if not sell_price:
            sell_price = base_price + tax_amount
            
        new_product = {
            "store_name": "Main Store",
            "product_name": data.get('product_name'),
            "brand": data.get('brand'),
            "category": data.get('category'),
            "price_quantity": data.get('price_quantity'),
            "product_unit": data.get('product_unit'),
            "cost_price": cost_price,
            "base_price": base_price,
            "tax_percent": tax_percent,
            "tax_amount": tax_amount,
            "profit_margin": sell_price - cost_price,
            "sell_price": sell_price,
            "stock": safe_int(data.get('stock')),
            "sold_stock": 0,
            "stock_status": data.get('stock_status', 'In Stock'),
            "product_status": "Active",
            "created_at": datetime.now().isoformat()
        }
        
        supabase.table('products').insert(new_product).execute()
        flash('Product added to Main Store!', 'success')
        return redirect(url_for('main_store.all_product'))
    except Exception as e:
        print(f"Error adding product: {e}")
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('main_store.add_product'))

@main_store_bp.route('/all-product')
def all_product():
    try:
        res = supabase.table('products').select('*').eq('store_name', 'Main Store').execute()
        products = res.data or []
    except:
        products = []
    return render_template('all_product_main.html', products=products)

@main_store_bp.route('/credit-customer')
def credit_customer():
    return redirect(url_for('customer.dashboard'))

@main_store_bp.route('/billing', methods=['GET', 'POST'])
def billing():
    if request.method == 'GET':
        try:
            res = supabase.table('products').select('*').eq('store_name', 'Main Store').eq('product_status', 'Active').execute()
            products = res.data or []
        except:
            products = []
        return render_template('billing_main.html', products=products)

    # POST Logic (Finalize Bill)
    try:
        data = request.get_json()
        items = data.get('items', [])
        if not items:
            return jsonify({'success': False, 'message': 'No items in cart'})

        total_quantity = 0
        subtotal_amount = 0
        total_tax_amount = 0
        bill_total = 0
        validated_items = []

        for item in items:
            p_id = item.get('product_id')
            p_qty = safe_float(item.get('quantity'))
            if not p_id or p_qty <= 0: continue

            res = supabase.table('products').select('*').eq('product_id', p_id).execute()
            if not res.data: continue
            
            prod = res.data[0]
            p_sell_price = safe_float(prod.get('sell_price'))
            p_tax_pct = safe_float(prod.get('tax_percent'))
            
            line_total = p_sell_price * p_qty
            base_price = line_total / (1 + (p_tax_pct/100))
            tax_amount = line_total - base_price
            
            bill_total += line_total
            subtotal_amount += base_price
            total_tax_amount += tax_amount
            total_quantity += p_qty
            
            validated_items.append({
                "product_id": p_id,
                "name": prod.get('product_name'),
                "quantity": p_qty,
                "stock_after": safe_float(prod.get('stock')) - p_qty,
                "sold_after": safe_float(prod.get('sold_stock', 0)) + p_qty,
                "line_total": line_total,
                "base_price": base_price,
                "tax_amount": tax_amount,
                "tax_percent": p_tax_pct,
                "final_price": p_sell_price
            })

        # Generate Bill No
        today_str = datetime.now().strftime("%Y%m%d")
        try:
            resp = supabase.table('bills').select('bill_id').order('bill_id', desc=True).limit(1).execute()
            last_id = resp.data[0].get('bill_id', 0) if resp.data else 0
        except: last_id = 0
        bill_no = f"MAIN-{today_str}-{last_id+1:04d}"

        new_bill = {
            "bill_no": bill_no,
            "store_name": "Main Store",
            "total_product": len(validated_items),
            "total_quantity": total_quantity,
            "subtotal_amount": round(subtotal_amount, 2),
            "total_tax_amount": round(total_tax_amount, 2),
            "bill_total": round(bill_total, 2),
            "payment_status": "Paid",
            "customer_name": data.get('customer_name', 'Cash'),
            "customer_phone": data.get('customer_phone', '-')
        }

        bill_resp = supabase.table('bills').insert(new_bill).execute()
        if not bill_resp.data: raise Exception("Failed to insert bill")
        
        bill_pk = bill_resp.data[0].get('bill_id')

        # Insert Items & Update Stock
        for v in validated_items:
            supabase.table('bill_items').insert({
                "bill_id": bill_pk,
                "product_id": v['product_id'],
                "product_name": v['name'],
                "quantity": v['quantity'],
                "base_price": v['base_price'],
                "tax_amount": v['tax_amount'],
                "tax_percent": v['tax_percent'],
                "final_price": v['final_price'],
                "total_price": v['line_total']
            }).execute()
            
            supabase.table('products').update({
                'stock': v['stock_after'],
                'sold_stock': v['sold_after']
            }).eq('product_id', v['product_id']).execute()

        return jsonify({'success': True, 'bill_no': bill_no})

    except Exception as e:
        print(f"Billing error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@main_store_bp.route('/revenues')
def revenues():
    return render_template('revenues_main.html')

@main_store_bp.route('/payments')
def payments():
    return render_template('payments_main.html')

@main_store_bp.route('/seller')
def seller():
    return redirect(url_for('seller.index'))

@main_store_bp.route('/employee')
def employee():
    return redirect(url_for('employee.index'))
