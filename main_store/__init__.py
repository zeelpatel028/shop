from flask import Blueprint

main_store_bp = Blueprint('main_store', __name__,
                          template_folder='templates',
                          static_folder='static')

from . import routes
