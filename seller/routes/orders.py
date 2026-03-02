from flask import render_template
from .. import seller_bp

@seller_bp.route('/orders')
def orders():
    return render_template('orders.html')

@seller_bp.route('/orders/pending')
def pending_orders():
    return render_template('pending_orders.html')

@seller_bp.route('/orders/complete')
def complete_orders():
    return render_template('complete_orders.html')

@seller_bp.route('/orders/return')
def return_orders():
    return render_template('return_orders.html')
