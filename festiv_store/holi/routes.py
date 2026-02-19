import os
import json
import collections
from flask import render_template, request, redirect, url_for, flash, jsonify
from .. import festiv_store_bp
from database.db import supabase

@festiv_store_bp.route('/holi')
def holi_dashboard():
    # Count documents using Supabase
    try:
        product_count = supabase.table('products').select('*', count='exact').execute().count
        bill_count = supabase.table('bills').select('*', count='exact').execute().count
        
        # Calculate total revenue
        # SQL: SELECT sum(total) FROM bills
        # Supabase API doesn't support sum() directly on select easily without rpc, 
        # so fetching all bills for now (since dataset is small) or we could use custom query if user allowed it.
        # Fetching all bills for calculation:
        bills_response = supabase.table('bills').select('total').execute()
        bills = bills_response.data
        total_revenue = sum(bill['total'] for bill in bills) if bills else 0

    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        product_count = 0
        bill_count = 0
        total_revenue = 0
    
    return render_template('holi.html', 
                         product_count=product_count, 
                         bill_count=bill_count, 
                         revenue=total_revenue)

@festiv_store_bp.route('/holi/master-stock')
def master_stock():
    try:
        products_response = supabase.table('products').select('*').execute()
        products = products_response.data
        
        bills_response = supabase.table('bills').select('*').execute()
        bills = bills_response.data
    except Exception as e:
        print(f"Error fetching master stock data: {e}")
        products = []
        bills = []
    
    # Calculate sales count for Most Sold
    product_sales = collections.defaultdict(int)
    for bill in bills:
        # Assuming bills have product_name, if normalized we need to join. 
        # Current schema puts product_name in bills for simplicity or bill_items. 
        # Checking if product_name exists in bill or if we need to fetch bill_items.
        # Based on schema.sql, bills has product_name.
        if 'product_name' in bill and bill['product_name']:
            product_sales[bill['product_name']] += bill.get('quantity', 0)
        
    # Attach sales to products for sorting (temporary attribute for template)
    for p in products:
        p['sales'] = product_sales.get(p['name'], 0) # Assuming 'name' field exists or 'product_name'
        
    most_sold = sorted(products, key=lambda x: x.get('sales', 0), reverse=True)
    low_stock = [p for p in products if p.get('stock', 0) <= 20]
    
    return render_template('master_stock.html', 
                         products=products, 
                         most_sold=most_sold,
                         low_stock=low_stock)

@festiv_store_bp.route('/holi/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        # Assuming product_id is the primary key or 'id' field
        supabase.table('products').delete().eq('id', product_id).execute()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        print(f"Error deleting product: {e}")
        flash('Error deleting product!', 'error')
        
    return redirect(url_for('festiv_store.master_stock'))

@festiv_store_bp.route('/holi/add-product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            # Auto-increment logic is handled by DB if using SERIAL, but user was using 'id' field manually
            # We can find max id if we want to retain 'id' column logic
            products_response = supabase.table('products').select('id').order('id', desc=True).limit(1).execute()
            if products_response.data:
                new_id = products_response.data[0]['id'] + 1
            else:
                new_id = 1

            # Get form data
            stock_qty = int(request.form.get('stock', 0))
            base_price = float(request.form.get('base_price', 0))
            offer_price = float(request.form.get('offer_price', 0)) if request.form.get('offer_price') else None
            cost_price = float(request.form.get('cost_price', 0)) if request.form.get('cost_price') else None
            tax_percent = float(request.form.get('tax_percent', 0)) if request.form.get('tax_percent') else 0
            
            # Simple tax calculation if needed, otherwise just store
            # final_price logic: if offer_price, use it, else base_price + tax? 
            # adhering to schema: base_price, tax_percent, tax_amount, final_price
            
            tax_amount = (base_price * tax_percent) / 100
            final_price = base_price + tax_amount
            if offer_price:
                 # If offer price is set, does it include tax? assuming final price is offer price for sale
                 final_price = offer_price

            new_product = {
                "id": new_id,
                "product_name": request.form.get('product_name'),
                "name": request.form.get('product_name'), # Backwards compatibility
                "product_category": request.form.get('product_category'),
                "category": request.form.get('product_category'), # Backwards compatibility
                
                "store_name": request.form.get('store_name'),
                "product_brand": request.form.get('product_brand'),
                
                "base_price": base_price,
                "price": base_price, # Backwards compatibility
                "offer_price": offer_price,
                "cost_price": cost_price,
                "tax_percent": tax_percent,
                "tax_amount": tax_amount,
                "final_price": final_price,
                
                "stock": stock_qty,
                "product_weight": float(request.form.get('product_weight', 0)) if request.form.get('product_weight') else None,
                "product_unit": request.form.get('product_unit'),
                
                "product_quantity": int(request.form.get('product_quantity', 1)) if request.form.get('product_quantity') else None,
                "price_quantity": request.form.get('price_quantity'),
                "profit_margin": float(request.form.get('profit_margin', 0)) if request.form.get('profit_margin') else None,
                
                "image": "Holi colours.jpg", # Placeholder if no file upload logic yet
                
                "product_status": request.form.get('product_status'),
                "stock_status": "InStock" if stock_qty > 0 else "OutOfStock"
            }
            supabase.table('products').insert(new_product).execute()
            flash('Product added successfully!', 'success')
        except Exception as e:
             print(f"Error adding product: {e}")
             flash('Error adding product!', 'error')
             
        return redirect(url_for('festiv_store.master_stock'))
    return render_template('add_product.html')

@festiv_store_bp.route('/holi/ledger')
def ledger():
    try:
        bills_response = supabase.table('bills').select('*').execute()
        bills = bills_response.data
    except Exception as e:
        print(f"Error fetching ledger: {e}")
        bills = []
    return render_template('ledger.html', bills=bills)

@festiv_store_bp.route('/holi/make-bill', methods=['GET', 'POST'])
def make_bill():
    if request.method == 'POST':
        try:
            data = request.get_json()
            items = data.get('items', [])
            customer_name = data.get('customer_name')
            customer_phone = data.get('customer_phone')
            
            if not items:
                return jsonify({'success': False, 'message': 'No items in cart'})

            # Calculate Totals
            total_items = len(items)
            total_quantity = sum(item['quantity'] for item in items)
            
            # Recalculate amounts on backend for security
            subtotal_amount = 0
            total_tax_amount = 0
            bill_total = 0
            
            # Validate Stock & Calculate
            for item in items:
                # Ideally fetch fresh product data here to verify stock and price
                # For this implementation, we'll verify stock at least
                prod_data = supabase.table('products').select('stock').eq('id', item['id']).single().execute()
                current_stock = prod_data.data['stock']
                
                if current_stock < item['quantity']:
                     return jsonify({'success': False, 'message': f"Insufficient stock for {item['name']}"})
                
                # Calculation (using frontend sent prices for now, but in production should use DB prices)
                final_price = item['final_price']
                qty = item['quantity']
                tax_percent = item['tax_percent']
                
                line_total = final_price * qty
                bill_total += line_total
                
                # Back-calculate base and tax
                base_total = line_total / (1 + (tax_percent/100))
                subtotal_amount += base_total
                tax_amount = line_total - base_total
                total_tax_amount += tax_amount

            # Generate Bill ID/No
            # Get max ID
            try:
                bills_resp = supabase.table('bills').select('id').order('id', desc=True).limit(1).execute()
                new_id = bills_resp.data[0]['id'] + 1 if bills_resp.data else 1
            except:
                new_id = 1
                
            bill_no = f"BILL{new_id:04d}"
            
            from datetime import datetime
            now = datetime.now()
            
            new_bill = {
                "id": new_id,
                "bill_no": bill_no,
                "store_name": "Holi Hub", # Default
                "total_items": total_items,
                "total_quantity": total_quantity,
                "subtotal_amount": round(subtotal_amount, 2),
                "total_tax_amount": round(total_tax_amount, 2),
                "bill_total": round(bill_total, 2),
                "total": round(bill_total, 2), # Legacy support
                "date": now.strftime("%Y-%m-%d"),
                "bill_date": now.strftime("%Y-%m-%d"),
                "bill_time": now.strftime("%H:%M:%S"),
                "payment_status": "Paid", # Default to paid for now
                "bill_status": "Completed"
            }
            
            # Insert Bill
            bill_insert_response = supabase.table('bills').insert(new_bill).execute()
            
            # Get the generated serial bill_id
            if bill_insert_response.data:
                bill_pk = bill_insert_response.data[0]['bill_id']
            else:
                 # Fallback if for some reason data isn't returned (shouldn't happen with default setup)
                 saved_bill = supabase.table('bills').select('bill_id').eq('id', new_id).single().execute()
                 bill_pk = saved_bill.data['bill_id']
            
            # Insert Bill Items & Update Stock
            for item in items:
                # Bill Item
                line_total = item['final_price'] * item['quantity']
                
                bill_item = {
                    "bill_id": bill_pk, 
                    "product_id": item['id'], 
                    "product_name": item['name'],
                    "quantity": item['quantity'],
                    "final_price": item['final_price'],
                    "total_price": line_total,
                    "tax_percent": item['tax_percent']
                }
                
                # Insert Item
                supabase.table('bill_items').insert(bill_item).execute()
                
                # Update Stock
                new_stock = item['stock'] - item['quantity']
                supabase.table('products').update({'stock': new_stock}).eq('id', item['id']).execute()

            return jsonify({'success': True, 'bill_no': bill_no})

        except Exception as e:
            print(f"Error making bill: {e}")
            return jsonify({'success': False, 'message': str(e)})

    # GET Request
    try:
        products_response = supabase.table('products').select('*').execute()
        products = products_response.data or []
    except:
        products = []
            
    return render_template('make_bill.html', products=products)

@festiv_store_bp.route('/holi-premium')
def holi_premium():
    return render_template('premium.html')
@festiv_store_bp.route('/holi/payment-data')
def payment_data():
    return render_template('payment_data.html')
