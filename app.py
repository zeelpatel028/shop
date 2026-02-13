from flask import Flask, render_template, request, redirect, url_for, flash
from festiv_store import festiv_store_bp

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for flashing messages

# Register Blueprints
app.register_blueprint(festiv_store_bp, url_prefix='/festiv_store')

# Hardcoded credentials as requested
USER_EMAIL = "zeelptl028@gmail.com"
USER_PASS = "tulshi"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/orders')
def orders():
    return render_template('orders.html')

@app.route('/customers')
def customers():
    return render_template('customers.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if email == USER_EMAIL and password == USER_PASS:
        return redirect(url_for('home'))
        # return f"<h1>Welcome, {email}! Login Successful.</h1>"
    else:
        # In a real app, you'd flash a message or return a specific error page
        return "<h1>Login Failed! Invalid Credentials. <a href='/'>Try again</a></h1>"

if __name__ == '__main__':
    app.run(debug=True)
