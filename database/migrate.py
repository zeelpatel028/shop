import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate():
    db_host = os.environ.get("DB_HOST", "dpg-d6g1fqlm5p6s7393ra9g-a.singapore-postgres.render.com")
    db_name = os.environ.get("DB_NAME", "shopdb_w6wu")
    db_user = os.environ.get("DB_USER", "shopdb")
    db_password = os.environ.get("DB_PASSWORD", "i8LGMATvuBiZ9qK7FRJT0HuncOmgMQVx")
    db_port = os.environ.get("DB_PORT", "5432")
    db_ssl_mode = os.environ.get("DB_SSL_MODE", "require")

    print(f"Connecting to {db_name} on {db_host}:{db_port} (SSL: {db_ssl_mode})...")
    
    try:
        # Establish connection
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port,
            sslmode=db_ssl_mode
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Read schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            sql = f.read()

        print("Executing schema.sql...")
        cur.execute(sql)
        
        print("Migration successful! Tables created.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
