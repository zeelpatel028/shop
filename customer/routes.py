from flask import render_template
from . import customer_bp

@customer_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

@customer_bp.route('/add')
def add_customer():
    return render_template('add_customer.html')

@customer_bp.route('/all')
def all_customers():
    return render_template('all_customers.html')

@customer_bp.route('/pending-bills')
def pending_bills():
    return render_template('pending_bills.html')

@customer_bp.route('/approve-bills')
def approve_bills():
    return render_template('approve_bills.html')
