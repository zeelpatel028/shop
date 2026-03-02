from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os # Force reload
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
    logger.info("Successfully registered festiv_store blueprint")
except ImportError as e:
    logger.error(f"Could not import festiv_store blueprint: {e}")

try:
    from main_store import main_store_bp
    app.register_blueprint(main_store_bp, url_prefix='/main_store')
    logger.info("Successfully registered main_store blueprint")
except ImportError as e:
    logger.error(f"Could not import main_store blueprint: {e}")

try:
    from customer import customer_bp
    app.register_blueprint(customer_bp, url_prefix='/customer')
    logger.info("Successfully registered customer blueprint")
except ImportError as e:
    logger.error(f"Could not import customer blueprint: {e}")

try:
    from employee import employee_bp
    app.register_blueprint(employee_bp, url_prefix='/employee')
    logger.info("Successfully registered employee blueprint")
except ImportError as e:
    logger.error(f"Could not import employee blueprint: {e}")

try:
    from seller import seller_bp
    app.register_blueprint(seller_bp, url_prefix='/seller')
    logger.info("Successfully registered seller blueprint")
except ImportError as e:
    logger.error(f"Could not import seller blueprint: {e}")

# --- PRODUCTION ENDPOINTS ---

@app.route('/health')
def health_check():
    """Health check endpoint for Render/Cloud monitoring."""
    return jsonify({
        "status": "healthy",
        "database": "connected" if DatabaseManager._pool else "disconnected"
    }), 200

@app.route('/ping')
def ping():
    """Lightweight ping endpoint."""
    return "pong", 200


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
    try:
        # Calculate Global Revenue (Only Paid Bills)
        bills_res = supabase.table('bills').select('*').order('created_at', desc=True).execute()
        all_bills = bills_res.data or []
        paid_bills = [b for b in all_bills if b.get('payment_status') == 'Paid']
        global_revenue = sum(float(b.get('bill_total') or 0) for b in paid_bills)
        
        # Calculate Customers Stats
        cust_res = supabase.table('customer').select('*').execute()
        customers = cust_res.data or []
        total_customers = len(customers)
        credit_customers = sum(1 for c in customers if int(c.get('panding_bill_count') or 0) > 0)
        
        # Determine active modules based on stores used
        stores_active = set(b.get('store_name') for b in all_bills if b.get('store_name'))
        active_modules = len(stores_active) if stores_active else 2 # default assuming Main & Festiv
        
        # Cross-store Recent Bills
        recent_activity = all_bills[:5]
        
    except Exception as e:
        logger.error(f"Error fetching global analytics: {e}")
        global_revenue = total_customers = credit_customers = active_modules = 0
        recent_activity = []

    return render_template('home.html', 
                         global_revenue=global_revenue,
                         total_customers=total_customers,
                         credit_customers=credit_customers,
                         active_modules=active_modules,
                         recent_activity=recent_activity)

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

# --- KEEP-ALIVE MECHANISM ---

def start_keep_alive():
    """Starts a background thread to ping the app and keep it alive on Render."""
    def ping_self():
        # Wait for the server to spin up
        logger.info("Keep-alive initialization: Waiting 10s for server startup...")
        time.sleep(300)
        
        # Priority: RENDER_EXTERNAL_URL > local URL
        url = os.environ.get('RENDER_EXTERNAL_URL')
        if not url:
            port = int(os.environ.get("PORT", 10000))
            url = f"http://127.0.0.1:{port}"
        
        ping_url = f"{url.rstrip('/')}/ping"
        logger.info(f"Keep-alive thread active. Target: {ping_url}")
        
        headers = {'User-Agent': 'TulshiShop-KeepAlive/1.0'}
        
        while True:
            try:
                response = requests.get(ping_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    # Successful ping
                    pass
                else:
                    logger.warning(f"Keep-alive ping returned status: {response.status_code}")
            except Exception as e:
                logger.error(f"Keep-alive ping error: {e}")
            
            # Ping every 5 minutes (300 seconds) as requested
            time.sleep(300)

    # Use a daemon thread so it exits when the main process does
    thread = threading.Thread(target=ping_self, daemon=True)
    thread.start()


if __name__ == '__main__':
    # Start keep-alive thread if on Render or explicitly requested
    if os.environ.get('RENDER') or os.environ.get('KEEP_ALIVE'):
        start_keep_alive()

    # Render environment provides PORT variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

