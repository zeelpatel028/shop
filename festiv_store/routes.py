from flask import render_template
from festiv_store import festiv_store_bp
from database.db import supabase

@festiv_store_bp.route('/')
def index():
    return render_template('festiv_store.html')
