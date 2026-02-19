from flask import Flask, render_template, request, redirect, url_for, flash
from festiv_store import festiv_store_bp

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for flashing messages

# Register Blueprints
app.register_blueprint(festiv_store_bp, url_prefix='/festiv_store')

# Initialize DB (Supabase)
from database.db import init_db
init_db(app)

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
