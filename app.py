from flask import Flask, render_template, request, redirect, url_for, flash
from festiv_store import festiv_store_bp

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for flashing messages

# Register Blueprints
app.register_blueprint(festiv_store_bp, url_prefix='/festiv_store')

# Initialize DB (Supabase)
from database.db import init_db
init_db(app)

# --- KEEP-ALIVE MECHANISM ---
import threading
import time
import requests

def keep_alive():
    """Pings the Render service every 10 seconds to prevent auto-spin down."""
    while True:
        try:
            requests.get('https://shop-d07d.onrender.com')
            print("Pinged https://shop-d07d.onrender.com successfully.")
        except Exception as e:
            print(f"Ping failed: {e}")
        time.sleep(10)

def start_keep_alive():
    thread = threading.Thread(target=keep_alive)
    thread.daemon = True
    thread.start()

start_keep_alive()
# ----------------------------

# Authorized Phone Numbers
AUTHORIZED_PHONES = ["6353807407", "9913887677"]
AUTHORIZED_PASSWORD = "tulshi"

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

    if phone in AUTHORIZED_PHONES and password == AUTHORIZED_PASSWORD:
        return redirect(url_for('home'))
    else:
        # In a real app, you'd flash a message or return a specific error page
        return "<h1>Login Failed! Invalid Phone Number or Password. <a href='/'>Try again</a></h1>"

if __name__ == '__main__':
    app.run(debug=True)
