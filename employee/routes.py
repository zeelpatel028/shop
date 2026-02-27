from flask import render_template
from . import employee_bp

@employee_bp.route('/')
def index():
    return render_template('dashboard.html')
