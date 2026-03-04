from flask import render_template, request, redirect, url_for, flash
from .. import main_store_bp
from database.db import supabase
from datetime import datetime
from collections import defaultdict

def safe_float(value, default=0.0):
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    try:
        if not value:
            return default
        return int(float(str(value))) if isinstance(value, (str, bytes)) else int(value)
    except (ValueError, TypeError, NameError):
        try:
            return int(float(value)) if value else default
        except:
            return default

@main_store_bp.route('/master-stock')
def master_stock():
    try:
        # Fetch active products for the main list
        active_products_response = supabase.table('products').select('*').eq('store_name', 'Main Store').eq('product_status', 'Active').execute()
        active_products = active_products_response.data or []
        
        # Fetch inactive products for the removed tab
        inactive_products_response = supabase.table('products').select('*').eq('store_name', 'Main Store').eq('product_status', 'Inactive').execute()
        inactive_products = inactive_products_response.data or []
        
        # Fetch bill_items for sales count
        items_response = supabase.table('bill_items').select('product_name, quantity').execute()
        bill_items = items_response.data or []
    except Exception as e:
        print(f"Error fetching master stock data: {e}")
        active_products = []
        inactive_products = []
        bill_items = []
    
    # Calculate sales count
    product_sales = defaultdict(int)
    for item in bill_items:
        if 'product_name' in item and item['product_name']:
            product_sales[item['product_name']] += item.get('quantity', 0)
        
    combined_products = active_products + inactive_products
    for p in combined_products:
        p['sales'] = product_sales.get(p.get('product_name'), 0)
        
    active_products = [p for p in combined_products if p.get('product_status', 'Active') == 'Active']
    inactive_products = [p for p in combined_products if p.get('product_status') == 'Inactive']
        
    most_sold = sorted(active_products, key=lambda x: x.get('sales', 0), reverse=True)
    low_stock = [p for p in active_products if p.get('stock', 0) <= 10]
    
    return render_template('master_stock_main.html', 
                         products=active_products, 
                         inactive_products=inactive_products,
                         most_sold=most_sold,
                         low_stock=low_stock)

@main_store_bp.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        items_check = supabase.table('bill_items').select('bill_item_id').eq('product_id', product_id).limit(1).execute()
        
        if items_check.data:
            supabase.table('products').update({'product_status': 'Inactive', 'stock_status': 'Out of Stock'}).eq('product_id', product_id).execute()
            flash('Product moved to Removed list (preserves sales history).', 'info')
        else:
            response = supabase.table('products').delete().eq('product_id', product_id).execute()
            if response.data:
                flash('Product deleted successfully!', 'success')
            else:
                flash('Product not found or could not be deleted!', 'warning')
            
    except Exception as e:
        flash(f'Error processing deletion: {str(e)}', 'error')
        
    return redirect(url_for('main_store.master_stock'))

@main_store_bp.route('/restore-product/<int:product_id>', methods=['POST'])
def restore_product(product_id):
    try:
        supabase.table('products').update({'product_status': 'Active', 'stock_status': 'In Stock'}).eq('product_id', product_id).execute()
        flash('Product restored successfully!', 'success')
    except Exception as e:
        flash('Error restoring product!', 'error')
    return redirect(url_for('main_store.master_stock'))

@main_store_bp.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'GET':
        return render_template('add_product_main.html')

    try:
        base_price = safe_float(request.form.get('base_price'))
        tax_percent = safe_float(request.form.get('tax_percent'))
        stock_qty = safe_int(request.form.get('stock'))
        sold_stock = safe_int(request.form.get('sold_stock', 0))

        operation_type = request.form.get('operation_type', 'add_new')

        if operation_type == 'add_new':
            cost_price = safe_float(request.form.get('cost_price'))
            sell_price = safe_float(request.form.get('sell_price'))
            tax_amount = (base_price * tax_percent) / 100

            if not sell_price:
                sell_price = base_price + tax_amount

            profit_margin = sell_price - cost_price

            new_product = {
                "store_name": "Main Store",
                "product_name": request.form.get('product_name'),
                "brand": request.form.get('brand'),
                "category": request.form.get('category'),
                "price_quantity": request.form.get('price_quantity'),
                "product_unit": request.form.get('product_unit'),
                "cost_price": cost_price,
                "base_price": base_price,
                "tax_percent": tax_percent,
                "tax_amount": tax_amount,
                "profit_margin": profit_margin,
                "sell_price": sell_price,
                "stock": stock_qty,
                "sold_stock": sold_stock,
                "stock_status": request.form.get('stock_status', 'In Stock'),
                "product_status": request.form.get('product_status', 'Active'),
                "last_updated_quantity": stock_qty,
                "seller_name": request.form.get('seller_name'),
                "name": request.form.get('name'),
                "created_at": datetime.now().isoformat()
            }

            supabase.table('products').insert(new_product).execute()
            flash('Product added successfully to Main Store!', 'success')

        elif operation_type == 'add_stock':
            existing_product_id = request.form.get('existing_product_id')
            qty_to_add = safe_int(request.form.get('stock'))
            
            if not existing_product_id or qty_to_add <= 0:
                flash('Valid product and quantity required for Add Stock', 'error')
                return redirect(url_for('main_store.add_product'))
                
            # Fetch existing product
            res = supabase.table('products').select('stock').eq('product_id', existing_product_id).execute()
            if not res.data:
                flash('Product not found', 'error')
                return redirect(url_for('main_store.add_product'))
                
            current_stock = safe_int(res.data[0].get('stock', 0))
            new_stock = current_stock + qty_to_add
            
            # Note: We aren't doing anything with stock_seller_name in DB yet as your schema 
            # doesn't link individual stock additions to sellers in a ledger yet, 
            # but we update the stock quantity.
            
            supabase.table('products').update({
                'stock': new_stock, 
                'last_updated_quantity': qty_to_add,
                'stock_status': 'In Stock' if new_stock > 0 else 'Out of Stock'
            }).eq('product_id', existing_product_id).execute()
            
            flash(f'Successfully added {qty_to_add} to stock!', 'success')

        elif operation_type == 'return_product':
            # This is complex: need to adjust bill, return product to stock, update customer/seller dues
            existing_product_id = request.form.get('existing_product_id')
            return_bill_id = request.form.get('return_bill_id')
            return_bill_product_id = request.form.get('return_bill_product_id') # Refers to bill_items.bill_item_id
            qty_to_return = safe_int(request.form.get('stock'))
            return_entity_type = request.form.get('return_entity_type', 'customer')
            
            if not existing_product_id or not return_bill_id or qty_to_return <= 0:
                flash('Valid product, bill, and quantity required for Return', 'error')
                return redirect(url_for('main_store.add_product'))
                
            # Fetch Product Stock
            res = supabase.table('products').select('stock, sold_stock').eq('product_id', existing_product_id).execute()
            if not res.data:
                flash('Product not found', 'error')
                return redirect(url_for('main_store.add_product'))
                
            current_stock = safe_int(res.data[0].get('stock', 0))
            current_sold = safe_int(res.data[0].get('sold_stock', 0))

            if return_entity_type == 'customer':
                # Customer returns item: Stock Increases
                supabase.table('products').update({
                    'stock': current_stock + qty_to_return,
                    'sold_stock': max(0, current_sold - qty_to_return),
                    'stock_status': 'In Stock'
                }).eq('product_id', existing_product_id).execute()
                
                if return_bill_product_id:
                    item_res = supabase.table('bill_items').select('*').eq('bill_item_id', return_bill_product_id).execute()
                    if item_res.data:
                        item = item_res.data[0]
                        new_qty = safe_int(item.get('quantity', 0)) - qty_to_return
                        
                        reduced_line_total = 0 # Amount to deduct from bill
                        reduced_tax = 0

                        if new_qty <= 0:
                            reduced_line_total = safe_float(item.get('total_price'))
                            reduced_tax = safe_float(item.get('tax_amount'))
                            supabase.table('bill_items').delete().eq('bill_item_id', return_bill_product_id).execute()
                        else:
                            base = safe_float(item.get('base_price'))
                            tax_p = safe_float(item.get('tax_percent'))
                            sell = safe_float(item.get('final_price'))
                            
                            old_line_total = safe_float(item.get('total_price'))
                            old_tax = safe_float(item.get('tax_amount'))

                            new_line_total = sell * new_qty
                            new_base_total = new_line_total / (1 + (tax_p/100))
                            new_tax_amount = new_line_total - new_base_total
                            
                            reduced_line_total = old_line_total - new_line_total
                            reduced_tax = old_tax - new_tax_amount

                            supabase.table('bill_items').update({
                                'quantity': new_qty,
                                'tax_amount': new_tax_amount,
                                'total_price': new_line_total
                            }).eq('bill_item_id', return_bill_product_id).execute()

                        # Update main bill totals
                        bill_res = supabase.table('bills').select('*').eq('bill_id', return_bill_id).execute()
                        if bill_res.data:
                            bill = bill_res.data[0]
                            supabase.table('bills').update({
                                'total_quantity': max(0, safe_int(bill.get('total_quantity')) - qty_to_return),
                                'total_tax_amount': max(0, safe_float(bill.get('total_tax_amount')) - reduced_tax),
                                'subtotal_amount': max(0, safe_float(bill.get('subtotal_amount')) - (reduced_line_total - reduced_tax)),
                                'bill_total': max(0, safe_float(bill.get('bill_total')) - reduced_line_total)
                            }).eq('bill_id', return_bill_id).execute()
                            
                            # Adjust credit bill and customer balance if applicable
                            cb_res = supabase.table('credit_bill').select('id, remaining_amount, total_price, c_id').eq('bill_id', return_bill_id).execute()
                            if cb_res.data:
                                cb = cb_res.data[0]
                                c_id = cb.get('c_id')
                                supabase.table('credit_bill').update({
                                    'total_price': max(0, safe_float(cb.get('total_price')) - reduced_line_total),
                                    'remaining_amount': max(0, safe_float(cb.get('remaining_amount')) - reduced_line_total)
                                }).eq('id', cb.get('id')).execute()
                                
                                # Optionally, we could adjust customer.padin_amount_total here too, but this is a good start.

            elif return_entity_type == 'seller':
                # Returning product to seller: Stock Decreases
                if current_stock < qty_to_return:
                    flash('Not enough stock to return to seller!', 'error')
                    return redirect(url_for('main_store.add_product'))
                
                new_stock = current_stock - qty_to_return
                supabase.table('products').update({
                    'stock': new_stock,
                    'stock_status': 'In Stock' if new_stock > 0 else 'Out of Stock'
                }).eq('product_id', existing_product_id).execute()
                
                # Note: Currently relying on simple stock subtraction for seller returns since 
                # orders to sellers aren't detailed in bill_items for easy rollback.
            
            flash(f'Successfully processed return for {qty_to_return} items!', 'success')

        return redirect(url_for('main_store.master_stock'))

    except Exception as e:
        flash(f'Error processing request: {str(e)}', 'error')
        return redirect(url_for('main_store.add_product'))

# ================= AJax Endpoints for UI Dropdowns =================
from flask import jsonify

@main_store_bp.route('/api/products')
def api_products():
    res = supabase.table('products').select('product_id, product_name, stock').eq('store_name', 'Main Store').eq('product_status', 'Active').execute()
    return jsonify({'success': True, 'data': res.data or []})

@main_store_bp.route('/api/sellers')
def api_sellers():
    term = request.args.get('q', '').lower()
    query = supabase.table('seller').select('id, name')
    res = query.execute()
    data = [s for s in (res.data or []) if term in str(s.get('name', '')).lower()]
    return jsonify({'success': True, 'data': data})

@main_store_bp.route('/api/customers')
def api_customers():
    term = request.args.get('q', '').lower()
    query = supabase.table('customer').select('id, name, phone_no')
    res = query.execute()
    data = [c for c in (res.data or []) if term in str(c.get('name', '')).lower() or term in str(c.get('phone_no', '')).lower()]
    return jsonify({'success': True, 'data': data})

@main_store_bp.route('/api/bills/customer/<path:name>')
def api_bills_by_customer(name):
    # Use .or_ to search both name and phone
    res = supabase.table('bills').select('bill_id, bill_no, bill_total, created_at') \
        .eq('store_name', 'Main Store') \
        .or_(f"customer_name.ilike.%{name}%,customer_phone.ilike.%{name}%") \
        .order('created_at', desc=True).limit(10).execute()
    return jsonify({'success': True, 'data': res.data or []})

@main_store_bp.route('/api/bills/seller/<path:name>')
def api_bills_by_seller(name):
    # Find matching sellers first
    sellers_res = supabase.table('seller').select('id').ilike('name', f'%{name}%').execute()
    seller_ids = [s['id'] for s in (sellers_res.data or [])]
    
    if not seller_ids:
        return jsonify({'success': True, 'data': []})
        
    # Orders table connects sellers to purchases/bills
    res = supabase.table('orders').select('id, bill_total, created_at, bill_id:id').in_('seller_id', seller_ids).eq('store_name', 'Main Store').order('created_at', desc=True).limit(10).execute()
    return jsonify({'success': True, 'data': res.data or []})

@main_store_bp.route('/api/bill_items/<int:bill_id>')
def api_bill_items(bill_id):
    res = supabase.table('bill_items').select('bill_item_id, product_id, product_name, quantity, final_price').eq('bill_id', bill_id).execute()
    return jsonify({'success': True, 'data': res.data or []})

@main_store_bp.route('/api/order_items/<int:order_id>')
def api_order_items(order_id):
    order_res = supabase.table('orders').select('bill_item_id').eq('id', order_id).execute()
    if not order_res.data or not order_res.data[0].get('bill_item_id'):
        return jsonify({'success': True, 'data': []})
        
    bill_item_id = order_res.data[0].get('bill_item_id')
    res = supabase.table('bill_items').select('bill_item_id, product_id, product_name, quantity, final_price').eq('bill_item_id', bill_item_id).execute()
    return jsonify({'success': True, 'data': res.data or []})
