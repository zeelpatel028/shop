import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
dsn = os.environ.get("DATABASE_URL")
if not dsn:
    print("No DATABASE_URL found.")
    exit(1)

try:
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS seller_name TEXT;")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS name TEXT;")
    conn.commit()
    print("Successfully added seller_name and name columns")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'cur' in locals(): cur.close()
    if 'conn' in locals(): conn.close()
