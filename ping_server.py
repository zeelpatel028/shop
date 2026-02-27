import requests
import time
import os
from dotenv import load_dotenv

# Load any .env settings if present
load_dotenv()

# The target URL of your Render application
URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://shop-d07d.onrender.com')
PING_URL = f"{URL.rstrip('/')}/ping"

print(f"--- Render Keep-Alive Script Started ---")
print(f"Target URL: {PING_URL}")
print(f"Interval: 10 seconds")
print(f"Press Ctrl+C to stop.")

def ping():
    try:
        response = requests.get(PING_URL, timeout=10)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if response.status_code == 200:
            print(f"[{timestamp}] Ping Successful! Status: {response.status_code}")
        else:
            print(f"[{timestamp}] Ping Returned Status: {response.status_code}")
    except Exception as e:
        print(f"[{timestamp}] Ping Failed: {e}")

if __name__ == "__main__":
    while True:
        ping()
        time.sleep(10)
