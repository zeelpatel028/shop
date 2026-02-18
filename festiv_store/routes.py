from flask import render_template
from . import festiv_store_bp

@festiv_store_bp.route('/')
def index():
    return render_template('festiv_store.html')
