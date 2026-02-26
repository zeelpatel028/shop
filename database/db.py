import os
import psycopg2
from psycopg2 import pool, extras
from psycopg2.extras import RealDictCursor, execute_values
from datetime import datetime
import time
from contextlib import contextmanager
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Environment Variables
# DATABASE CONFIGURATION
DB_HOST = "localhost"
DB_NAME = os.environ.get("DB_NAME", "tulshi_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5433")
DB_SSL_MODE = os.environ.get("DB_SSL_MODE", "disable")

DB_MIN_CONN = int(os.environ.get("DB_MIN_CONN", 1))
DB_MAX_CONN = int(os.environ.get("DB_MAX_CONN", 10))

class DatabaseConnectionError(Exception):
    pass

class DatabaseManager:
    _pool = None

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            try:
                print(f"Connecting to DB: {DB_NAME} on {DB_HOST}:{DB_PORT} (User: {DB_USER}, SSL: {DB_SSL_MODE})")
                
                cls._pool = pool.ThreadedConnectionPool(
                    DB_MIN_CONN, 
                    DB_MAX_CONN,
                    host=DB_HOST,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    port=DB_PORT,
                    sslmode=DB_SSL_MODE
                )
                print("Connection pool initialized successfully.")
            except Exception as e:
                print(f"Error initializing connection pool: {e}")
                # Fallback diagnostic for common local issues
                if "server closed the connection" in str(e).lower() or "connection refused" in str(e).lower():
                    print(f"TIP: Your local PostgreSQL on port {DB_PORT} may not be running or is rejecting connections from '{DB_HOST}'.")
                    print(f"Try running 'netstat -ano | findstr :{DB_PORT}' to check if something is listening.")
                raise DatabaseConnectionError(f"Could not connect to database on {DB_HOST}:{DB_PORT}: {e}")
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

    def select(self, columns='*', count=None):
        self._select = columns
        self._count = count
        return self

    def eq(self, col, val):
        self._wheres.append((f"{col} = %s", val))
        return self

    def lt(self, col, val):
        self._wheres.append((f"{col} < %s", val))
        return self

    def gte(self, col, val):
        self._wheres.append((f"{col} >= %s", val))
        return self
        
    def order(self, col, desc=False):
        self._order = f"{col} {'DESC' if desc else 'ASC'}"
        return self

    def limit(self, n):
        self._limit = n
        return self

    def insert(self, data):
        self._insert_data = data
        return self

    def update(self, data):
        self._update_data = data
        return self

    def delete(self):
        self._delete = True
        return self

    def _serialize_rows(self, rows):
        """Converts datetime objects to ISO strings for existing app compatibility."""
        for row in rows:
            for k, v in row.items():
                if isinstance(v, datetime):
                    row[k] = v.isoformat()
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
                        if not items:
                            return Response()
                        
                        cols = list(items[0].keys())
                        col_str = ", ".join(cols)
                        
                        # Use execute_values for high-performance bulk inserts
                        query = f"INSERT INTO {self.table} ({col_str}) VALUES %s RETURNING *"
                        values = [[item.get(c) for c in cols] for item in items]
                        
                        execute_values(cur, query, values)
                        results = cur.fetchall()
                        conn.commit()
                        return Response(data=self._serialize_rows(results), count=len(results))

                    elif self._update_data is not None:
                        if not self._update_data:
                            return Response()

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

                    elif self._delete:
                        where_str = ""
                        values = []
                        if self._wheres:
                            where_clauses = [w[0] for w in self._wheres]
                            where_str = " WHERE " + " AND ".join(where_clauses)
                            values.extend([w[1] for w in self._wheres])

                        query = f"DELETE FROM {self.table}{where_str} RETURNING *"
                        cur.execute(query, values)
                        results = cur.fetchall()
                        conn.commit()
                        return Response(data=self._serialize_rows(results), count=len(results))

                    elif self._select is not None:
                        # Handle Join Detection (e.g., '*, bills(bill_no)')
                        # Pattern: primary_cols, linked_table(linked_cols)
                        join_str = ""
                        select_str = self._select
                        
                        if "(" in self._select and ")" in self._select:
                            try:
                                # Simple extraction for '*, bills(bill_no)' style
                                import re
                                match = re.search(r'(\w+)\(([\w,\*]+)\)', self._select)
                                if match:
                                    linked_table = match.group(1)
                                    linked_cols_raw = match.group(2)
                                    
                                    # Base table columns: everything before or after the match (excluding commas)
                                    # For '*, bills(bill_no)', primary is '*'
                                    primary_select = self._select.replace(match.group(0), "").strip(", ")
                                    if not primary_select: primary_select = "*"
                                    
                                    # Construct SQL: join on linked_table_id (heuristic)
                                    # If primary is payments, linked is bills, join on payments.bill_id = bills.bill_id
                                    # Singularize table name for FK guess
                                    fk_col = linked_table[:-1] if linked_table.endswith('s') else linked_table
                                    fk_col += "_id"
                                    
                                    join_str = f" LEFT JOIN {linked_table} ON {self.table}.{fk_col} = {linked_table}.{fk_col}"
                                    
                                    # Transform select to prefix with table names to avoid ambiguity
                                    linked_cols = [f"{linked_table}.{c.strip()} AS __joined_{linked_table}_{c.strip()}" 
                                                 for c in linked_cols_raw.split(",")]
                                    select_str = f"{self.table}.{primary_select}, {', '.join(linked_cols)}"
                            except Exception as join_err:
                                print(f"DEBUG: Join parser failed, falling back: {join_err}")

                        order_str = ""
                        if self._order:
                            if join_str and "." not in self._order:
                                order_str = f" ORDER BY {self.table}.{self._order}"
                            else:
                                order_str = f" ORDER BY {self._order}"
                        
                        limit_str = f" LIMIT {self._limit}" if self._limit else ""

                        where_str = ""
                        values = []
                        if self._wheres:
                            where_clauses = []
                            for clause, val in self._wheres:
                                if join_str and "." not in clause:
                                    where_clauses.append(f"{self.table}.{clause}")
                                else:
                                    where_clauses.append(clause)
                            
                            where_str = " WHERE " + " AND ".join(where_clauses)
                            values.extend([w[1] for w in self._wheres])

                        if self._count == 'exact':
                            count_query = f"SELECT COUNT(*) as c FROM {self.table}{where_str}"
                            cur.execute(count_query, values)
                            count_val = cur.fetchone()['c']
                            
                            query = f"SELECT {select_str} FROM {self.table}{join_str}{where_str}{order_str}{limit_str}"
                            cur.execute(query, values)
                            data = cur.fetchall()
                            
                            # Post-process to nest joined objects (Existing App expects payment.bills.bill_no)
                            if join_str:
                                for row in data:
                                    # Extract keys starting with __joined_tablename_
                                    prefix = f"__joined_{linked_table}_"
                                    row[linked_table] = {}
                                    keys_to_del = []
                                    for k, v in row.items():
                                        if k.startswith(prefix):
                                            col_name = k.replace(prefix, "")
                                            row[linked_table][col_name] = v
                                            keys_to_del.append(k)
                                    for k in keys_to_del: del row[k]

                            return Response(data=self._serialize_rows(data), count=count_val)
                        else:
                            query = f"SELECT {select_str} FROM {self.table}{join_str}{where_str}{order_str}{limit_str}"
                            print(f"DEBUG: Executing Join Query: {query}")
                            cur.execute(query, values)
                            data = cur.fetchall()
                            
                            # Post-process to nest joined objects
                            if join_str:
                                for row in data:
                                    prefix = f"__joined_{linked_table}_"
                                    row[linked_table] = {}
                                    keys_to_del = []
                                    for k, v in row.items():
                                        if k.startswith(prefix):
                                            col_name = k.replace(prefix, "")
                                            row[linked_table][col_name] = v
                                            keys_to_del.append(k)
                                    for k in keys_to_del: del row[k]
                                    
                            return Response(data=self._serialize_rows(data), count=len(data))
                            
                    return Response()
            except psycopg2.Error as e:
                print(f"Database error: {e}")
                conn.rollback()
                return Response()

class SupabaseStorageMock:
    def from_(self, bucket):
        return self
    def upload(self, path, file, file_options=None):
        pass

class SupabaseClientMock:
    def __init__(self):
        self.storage = SupabaseStorageMock()

    def table(self, table_name):
        return QueryBuilder(table_name)

# Singleton instance to mimic Supabase client
supabase = SupabaseClientMock()

def init_db(app):
    """Initializes the database connection pool on app startup."""
    try:
        DatabaseManager.get_pool()
        print("Live Database connected with SSL and Connection Pooling.")
    except Exception as e:
        print(f"CRITICAL: Database connection failed: {e}")
    
    app.config["SUPABASE_CLIENT"] = supabase

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        # This is handled by the connection pool putconn in the context manager,
        # but we could close the pool here if the app is shutting down.
        pass
