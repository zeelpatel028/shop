from flask import Blueprint

holi_store_bp = Blueprint('holi_store', __name__,
                          template_folder='templates',
                          static_folder='static',
                          static_url_path='/holi_store/static')

from . import routes
