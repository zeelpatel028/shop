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
            "created_at": datetime.now().isoformat()
        }

        supabase.table('products').insert(new_product).execute()

        flash('Product added successfully to Main Store!', 'success')
        return redirect(url_for('main_store.master_stock'))

    except Exception as e:
        flash(f'Error adding product: {str(e)}', 'error')
        return redirect(url_for('main_store.add_product'))
