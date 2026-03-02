from flask import Blueprint

seller_bp = Blueprint('seller', __name__,
                     template_folder='templates',
                     static_folder='static')

from .routes import *
