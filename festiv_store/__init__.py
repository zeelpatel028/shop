from flask import Blueprint, render_template

festiv_store_bp = Blueprint('festiv_store', __name__,
                            template_folder='templates',
                            static_folder='static',
                            static_url_path='/festiv_store/static')

from . import routes
