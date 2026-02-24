from flask import render_template
from . import main_store_bp

@main_store_bp.route('/')
def index():
    return render_template('main_store.html')

@main_store_bp.route('/add-product')
def add_product():
    return "<h1>Coming Soon: Add Product</h1><a href='/main_store'>Back</a>"

@main_store_bp.route('/all-product')
def all_product():
    return "<h1>Coming Soon: All Product</h1><a href='/main_store'>Back</a>"

@main_store_bp.route('/credit-customer')
def credit_customer():
    return "<h1>Coming Soon: Credit Customer</h1><a href='/main_store'>Back</a>"

@main_store_bp.route('/billing')
def billing():
    return "<h1>Coming Soon: Billing</h1><a href='/main_store'>Back</a>"

@main_store_bp.route('/revenues')
def revenues():
    return "<h1>Coming Soon: Revenues</h1><a href='/main_store'>Back</a>"

@main_store_bp.route('/payments')
def payments():
    return "<h1>Coming Soon: Payments</h1><a href='/main_store'>Back</a>"

@main_store_bp.route('/seller')
def seller():
    return "<h1>Coming Soon: Seller</h1><a href='/main_store'>Back</a>"

@main_store_bp.route('/employee')
def employee():
    return "<h1>Coming Soon: Employee</h1><a href='/main_store'>Back</a>"
