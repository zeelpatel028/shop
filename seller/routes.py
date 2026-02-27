from flask import render_template
from . import seller_bp

@seller_bp.route('/')
def index():
    return render_template('dashboard.html')
