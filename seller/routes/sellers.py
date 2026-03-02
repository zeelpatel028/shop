from flask import render_template
from .. import seller_bp

@seller_bp.route('/add')
def add_seller():
    return render_template('add_seller.html')

@seller_bp.route('/all')
def all_sellers():
    return render_template('all_sellers.html')
