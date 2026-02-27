from flask import Blueprint

employee_bp = Blueprint('employee', __name__,
                       template_folder='templates',
                       static_folder='static')

from . import routes
