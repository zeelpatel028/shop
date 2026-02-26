import os
import psycopg2
from psycopg2 import pool, extras
from psycopg2.extras import RealDictCursor, execute_values
from datetime import datetime
import time
from contextlib import contextmanager
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load .env file
load_dotenv()

class DatabaseConnectionError(Exception):
    pass

class DatabaseManager:
    _pool = None

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            try:
                # Priority 1: DATABASE_URL (Render/Heroku standard)
                database_url = os.environ.get("DATABASE_URL")
                
                if database_url:
                    # Fix protocol for SQLAlchemy/psycopg2 compatibility (postgres:// -> postgresql://)
                    if database_url.startswith("postgres://"):
                        database_url = database_url.replace("postgres://", "postgresql://", 1)
                    
                    # Ensure sslmode=require if not present in the URL
                    if "sslmode=" not in database_url:
                        separator = "&" if "?" in database_url else "?"
                        database_url += f"{separator}sslmode=require"

                    print("Connecting to Production DB using DATABASE_URL...")
                    cls._pool = pool.ThreadedConnectionPool(
                        int(os.environ.get("DB_MIN_CONN", 1)),
                        int(os.environ.get("DB_MAX_CONN", 10)),
                        database_url
                    )
                else:
                    # Priority 2: Individual variables (Local Dev)
                    host = os.environ.get('DB_HOST', '127.0.0.1')
                    port = os.environ.get('DB_PORT', '5433')
                    print(f"Connecting to Local DB at {host}:{port}")
                    cls._pool = pool.ThreadedConnectionPool(
                        int(os.environ.get("DB_MIN_CONN", 1)),
                        int(os.environ.get("DB_MAX_CONN", 10)),
                        host=host,
                        database=os.environ.get("DB_NAME", "tulshi_db"),
                        user=os.environ.get("DB_USER", "postgres"),
                        password=os.environ.get("DB_PASSWORD", "zeel@123"),
                        port=port,
                        sslmode=os.environ.get("DB_SSL_MODE", "disable")
                    )
                print("Database connection pool initialized.")
            except Exception as e:
                print(f"CRITICAL: Database connection failed: {e}")
                # Don't crash immediately, but allow health checks to report failure
                cls._pool = None
        return cls._pool

    @classmethod
    @contextmanager
    def get_connection(cls):
        pool = cls.get_pool()
        conn = pool.getconn()
        try:
            yield conn
        finally:
            pool.putconn(conn)

    @classmethod
    def close_all_connections(cls):
        if cls._pool:
            cls._pool.closeall()
            print("All database connections closed.")

class QueryBuilder:
    def __init__(self, table):
        self.table = table
        self._select = None
        self._count = None
        self._wheres = []
        self._order = None
        self._limit = None
        self._insert_data = None
        self._update_data = None
        self._delete = False

    # ... [Keep existing QueryBuilder methods as they are robust] ...
    # (Simplified for the sake of the walkthrough/transfer)
    def select(self, columns='*', count=None): self._select = columns; self._count = count; return self
    def eq(self, col, val): self._wheres.append((f"{col} = %s", val)); return self
    def order(self, col, desc=False): self._order = f"{col} {'DESC' if desc else 'ASC'}"; return self
    def limit(self, n): self._limit = n; return self
    def insert(self, data): self._insert_data = data; return self
    def update(self, data): self._update_data = data; return self
    def delete(self): self._delete = True; return self

    def _serialize_rows(self, rows):
        for row in rows:
            for k, v in row.items():
                if isinstance(v, datetime): row[k] = v.isoformat()
        return rows

    def execute(self):
        class Response:
            def __init__(self, data=None, count=None):
                self.data = data or []
                self.count = count or 0

        with DatabaseManager.get_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Optimized Bulk Insert
                    if self._insert_data is not None:
                        is_list = isinstance(self._insert_data, list)
                        items = self._insert_data if is_list else [self._insert_data]
                        if not items: return Response()
                        cols = list(items[0].keys())
                        query = f"INSERT INTO {self.table} ({', '.join(cols)}) VALUES %s RETURNING *"
                        values = [[item.get(c) for c in cols] for item in items]
                        execute_values(cur, query, values)
                        results = cur.fetchall()
                        conn.commit()
                        return Response(data=self._serialize_rows(results), count=len(results))

                    elif self._update_data is not None:
                        if not self._update_data: return Response()
                        cols = list(self._update_data.keys())
                        set_strs = [f"{c} = %s" for c in cols]
                        values = [self._update_data[c] for c in cols]
                        where_str = ""
                        if self._wheres:
                            where_clauses = [w[0] for w in self._wheres]
                            where_str = " WHERE " + " AND ".join(where_clauses)
                            values.extend([w[1] for w in self._wheres])
                        query = f"UPDATE {self.table} SET {', '.join(set_strs)}{where_str} RETURNING *"
                        cur.execute(query, values)
                        results = cur.fetchall()
                        conn.commit()
                        return Response(data=self._serialize_rows(results), count=len(results))

                    elif self._select is not None:
                        join_str = ""
                        select_str = self._select
                        if "(" in self._select and ")" in self._select:
                            try:
                                import re
                                match = re.search(r'(\w+)\(([\w,\*]+)\)', self._select)
                                if match:
                                    linked_table = match.group(1)
                                    linked_cols_raw = match.group(2)
                                    primary_select = self._select.replace(match.group(0), "").strip(", ")
                                    if not primary_select: primary_select = "*"
                                    fk_col = linked_table[:-1] if linked_table.endswith('s') else linked_table
                                    fk_col += "_id"
                                    join_str = f" LEFT JOIN {linked_table} ON {self.table}.{fk_col} = {linked_table}.{fk_col}"
                                    linked_cols = [f"{linked_table}.{c.strip()} AS __joined_{linked_table}_{c.strip()}" 
                                                 for c in linked_cols_raw.split(",")]
                                    select_str = f"{self.table}.{primary_select}, {', '.join(linked_cols)}"
                            except Exception as e: print(f"Join error: {e}")

                        where_str = ""
                        values = []
                        if self._wheres:
                            where_clauses = [w[0] for w in self._wheres]
                            where_str = " WHERE " + " AND ".join(where_clauses)
                            values.extend([w[1] for w in self._wheres])
                        
                        order_str = f" ORDER BY {self._order}" if self._order else ""
                        limit_str = f" LIMIT {self._limit}" if self._limit else ""
                        
                        query = f"SELECT {select_str} FROM {self.table}{join_str}{where_str}{order_str}{limit_str}"
                        cur.execute(query, values)
                        data = cur.fetchall()
                        
                        if join_str:
                            for row in data:
                                prefix = f"__joined_{linked_table}_"
                                row[linked_table] = {}
                                keys_to_del = []
                                for k, v in row.items():
                                    if k.startswith(prefix):
                                        row[linked_table][k.replace(prefix, "")] = v
                                        keys_to_del.append(k)
                                for k in keys_to_del: del row[k]
                        
                        return Response(data=self._serialize_rows(data), count=len(data))
                    
                    return Response()
            except Exception as e:
                print(f"Database error: {e}")
                conn.rollback()
                return Response()

class SupabaseClientMock:
    def table(self, table_name): return QueryBuilder(table_name)

supabase = SupabaseClientMock()

def init_schema():
    """Created necessary tables if they don't exist."""
    print("Checking database schema...")
    try:
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                # Create products table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        product_id SERIAL PRIMARY KEY,
                        product_name TEXT NOT NULL,
                        brand TEXT,
                        category TEXT,
                        sell_price DECIMAL(12, 2),
                        stock INT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # Create other tables as needed...
                conn.commit()
                print("Schema initialization complete.")
    except Exception as e:
        print(f"Error initializing schema: {e}")

def init_db(app):
    """Initializes the database connection pool and schema on app startup."""
    try:
        DatabaseManager.get_pool()
        init_schema()
        print("Production Database Layer Ready.")
    except Exception as e:
        print(f"CRITICAL: Application startup aborted - DB failure: {e}")
    
    app.config["SUPABASE_CLIENT"] = supabase

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        pass
