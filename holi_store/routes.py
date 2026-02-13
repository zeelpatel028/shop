from flask import render_template
from . import holi_store_bp

@holi_store_bp.route('/')
def index():
    return render_template('holi_store/index.html')
