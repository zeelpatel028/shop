import os
import json
import collections
from flask import render_template, request, redirect, url_for, flash
from .. import festiv_store_bp

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.json')
BILLS_FILE = os.path.join(DATA_DIR, 'bills.json')

def load_data(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        return json.load(f)

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

@festiv_store_bp.route('/holi')
def holi_dashboard():
    products = load_data(PRODUCTS_FILE)
    bills = load_data(BILLS_FILE)
    total_revenue = sum(bill['total'] for bill in bills)
    return render_template('holi.html', 
                         product_count=len(products), 
                         bill_count=len(bills), 
                         revenue=total_revenue)

@festiv_store_bp.route('/holi/master-stock')
def master_stock():
    products = load_data(PRODUCTS_FILE)
    bills = load_data(BILLS_FILE)
    
    # Calculate sales count for Most Sold
    product_sales = collections.defaultdict(int)
    for bill in bills:
        product_sales[bill['product_name']] += bill['quantity']
        
    # Attach sales to products for sorting (temporary attribute for template)
    for p in products:
        p['sales'] = product_sales.get(p['name'], 0)
        
    most_sold = sorted(products, key=lambda x: x['sales'], reverse=True)
    low_stock = [p for p in products if p['stock'] <= 20]
    
    return render_template('master_stock.html', 
                         products=products, 
                         most_sold=most_sold,
                         low_stock=low_stock)

@festiv_store_bp.route('/holi/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    products = load_data(PRODUCTS_FILE)
    # Filter out product with matching ID
    products = [p for p in products if p['id'] != product_id]
    save_data(PRODUCTS_FILE, products)
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('festiv_store.master_stock'))

@festiv_store_bp.route('/holi/add-product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        products = load_data(PRODUCTS_FILE)
        new_product = {
            "id": len(products) + 1,
            "name": request.form.get('name'),
            "category": request.form.get('category'),
            "price": float(request.form.get('price')),
            "stock": int(request.form.get('stock')),
            "image": "Holi colours.jpg"
        }
        products.append(new_product)
        save_data(PRODUCTS_FILE, products)
        flash('Product added successfully!', 'success')
        return redirect(url_for('festiv_store.master_stock'))
    return render_template('add_product.html')

@festiv_store_bp.route('/holi/ledger')
def ledger():
    bills = load_data(BILLS_FILE)
    return render_template('ledger.html', bills=bills)

@festiv_store_bp.route('/holi/make-bill', methods=['GET', 'POST'])
def make_bill():
    products = load_data(PRODUCTS_FILE)
    if request.method == 'POST':
        bills = load_data(BILLS_FILE)
        selected_product_id = int(request.form.get('product_id'))
        quantity = int(request.form.get('quantity'))
        
        product = next((p for p in products if p['id'] == selected_product_id), None)
        if product and product['stock'] >= quantity:
            total = product['price'] * quantity
            new_bill = {
                "id": len(bills) + 1,
                "product_name": product['name'],
                "quantity": quantity,
                "price": product['price'],
                "total": total,
                "date": "2026-02-18" # Simplified date
            }
            bills.append(new_bill)
            
            # Update stock
            product['stock'] -= quantity
            save_data(PRODUCTS_FILE, products)
            save_data(BILLS_FILE, bills)
            
            flash('Bill generated successfully!', 'success')
            return redirect(url_for('festiv_store.ledger'))
        else:
            flash('Insufficient stock or invalid product!', 'error')
            
    return render_template('make_bill.html', products=products)

@festiv_store_bp.route('/holi-premium')
def holi_premium():
    return render_template('premium.html')
@festiv_store_bp.route('/holi/payment-data')
def payment_data():
    return render_template('payment_data.html')
