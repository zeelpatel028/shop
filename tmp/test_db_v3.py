from database.db import supabase
import re

def test_prefixing():
    print("Testing Table Name Prefixing...")
    
    # Mocking DatabaseManager.get_connection to avoid actual DB connection
    
    def get_query_with_where(qb):
        # Simplified internal logic to extract generated WHERE and JOIN clauses
        # (This matches the logic I just added to db.py)
        table = qb.table
        wheres = qb._wheres
        where_clauses = [f"{table}.{w[0]}" if "." not in w[0] and "(" not in w[0] else w[0] for w in wheres]
        where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Join logic
        join_str = ""
        if "(" in qb._select and ")" in qb._select:
             match = re.search(r'(\w+)[!:]?(\w+)?\(([\w,\*]+)\)', qb._select)
             if match:
                linked_table = match.group(1)
                custom_fk = match.group(2)
                singular = linked_table[:-1] if linked_table.endswith('s') else linked_table
                fk_col = custom_fk if custom_fk else f"{singular}_id"
                target_pk_guess = f"{singular}_id"
                target_pk = target_pk_guess if fk_col == target_pk_guess else "id"
                join_str = f" JOIN {linked_table} ON {table}.{fk_col} = {linked_table}.{target_pk}"
        
        order_str = f" ORDER BY {table}.{qb._order}" if qb._order and "." not in qb._order else (f" ORDER BY {qb._order}" if qb._order else "")
        
        return f"JOIN: {join_str} | WHERE: {where_str} | ORDER: {order_str}"

    # Test case: payments query from payments.py
    qb = supabase.table('payments').select('*, bills!bill_id(bill_no)').eq('store_name', 'Main Store').order('created_at', desc=True)
    
    result = get_query_with_where(qb)
    print(f"Result: {result}")
    
    expected_where = " WHERE payments.store_name = %s"
    expected_order = " ORDER BY payments.created_at DESC"
    
    if expected_where in result and expected_order in result:
        print("Success: Correctly prefixed store_name and created_at with 'payments.'")
    else:
        print("Failure: Missing prefixes in some clauses.")

if __name__ == "__main__":
    test_prefixing()
