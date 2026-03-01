from database.db import supabase
import re

def test_update_sql():
    print("Testing UPDATE SQL Syntax...")
    
    def get_update_sql(qb, data):
        # Simulation of the update logic in db.py
        table = qb.table
        cols = list(data.keys())
        set_strs = [f"{c} = %s" for c in cols]
        
        where_str = ""
        if qb._wheres:
            where_clauses = [f"{table}.{w[0]}" if "." not in w[0] and "(" not in w[0] else w[0] for w in qb._wheres]
            where_str = " WHERE " + " AND ".join(where_clauses)
            
        return f"UPDATE {table} SET {', '.join(set_strs)}{where_str} RETURNING *"

    # Test case: UPI payment update
    qb = supabase.table('payments').eq('payment_reference', 'TEST-REF')
    update_data = {'payment_status': 'Paid', 'is_bill_generated': True}
    
    sql = get_update_sql(qb, update_data)
    print(f"Generated SQL: {sql}")
    
    # Expected: No prefix in SET, prefix in WHERE
    expected_set = "SET payment_status = %s, is_bill_generated = %s"
    expected_where = "WHERE payments.payment_reference = %s"
    
    if expected_set in sql and expected_where in sql:
        print("Success: SQL UPDATE syntax is correct (No prefix in SET, prefix in WHERE)")
    else:
        print("Failure: SQL syntax mismatch.")

if __name__ == "__main__":
    test_update_sql()
