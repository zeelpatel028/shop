from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import logging
import threading
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretproductionkey')

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DB (Cloud Optimized)
from database.db import init_db, supabase, DatabaseManager
init_db(app)

# Register Blueprints
try:
    from festiv_store import festiv_store_bp
    app.register_blueprint(festiv_store_bp, url_prefix='/festiv_store')
except ImportError:
    logger.warning("festiv_store blueprint not found. Skipping registration.")

try:
    from main_store import main_store_bp
    app.register_blueprint(main_store_bp, url_prefix='/main_store')
except ImportError:
    logger.warning("main_store blueprint not found. Skipping registration.")

# --- PRODUCTION ENDPOINTS ---

@app.route('/health')
def health_check():
    """Health check endpoint for Render/Cloud monitoring."""
    return jsonify({
        "status": "healthy",
        "database": "connected" if DatabaseManager._pool else "disconnected"
    }), 200

@app.route('/db-test')
def db_test():
    """Diagnostic endpoint to verify database connectivity."""
    try:
        res = supabase.table('products').select('*').limit(1).execute()
        return jsonify({"status": "success", "data_count": len(res.data)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- APP ROUTES ---

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    phone = request.form.get('phone')
    password = request.form.get('password')
    
    auth_phones = os.getenv("AUTHORIZED_PHONES", "6353807407,9913887677").split(",")
    auth_pass = os.getenv("AUTHORIZED_PASSWORD", "tulshi")

    if phone in auth_phones and password == auth_pass:
        return redirect(url_for('home'))
    
    flash("Invalid credentials", "danger")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Force use of port 5000 and 0.0.0.0 for Render compatibility locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
