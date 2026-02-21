from flask import Blueprint, render_template

festiv_store_bp = Blueprint('festiv_store', __name__,
                            template_folder='holi/templates',
                            static_folder='holi/static')

from . import routes as main_routes
from .holi.static.python import routes as holi_routes
