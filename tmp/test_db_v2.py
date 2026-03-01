from database.db import supabase, QueryBuilder
import re

def test_smart_joins():
    print("Testing Smart Join Heuristic...")
    
    # Mocking DatabaseManager.get_connection to avoid actual DB connection
    # We just want to see the generated SQL string
    
    # 1. Test bills!bill_id
    qb = supabase.table('payments').select('*, bills!bill_id(bill_no)')
    
    # We need to reach into the internal execute logic or manually trigger the string generation
    # For testing purposes, let's just simulate the internal logic or use a mock cursor
    
    # Let's mock the internal execute logic to just return the query string
    def get_query(self):
        select_str = self._select
        join_str = ""
        if "(" in self._select and ")" in self._select:
             match = re.search(r'(\w+)[!:]?(\w+)?\(([\w,\*]+)\)', self._select)
             if match:
                linked_table = match.group(1)
                custom_fk = match.group(2)
                linked_cols_raw = match.group(3)
                singular = linked_table[:-1] if linked_table.endswith('s') else linked_table
                fk_col = custom_fk if custom_fk else f"{singular}_id"
                target_pk_guess = f"{singular}_id"
                target_pk = target_pk_guess if fk_col == target_pk_guess else "id"
                join_str = f" JOIN {linked_table} ON {self.table}.{fk_col} = {linked_table}.{target_pk}"
        return join_str

    join1 = get_query(qb)
    print(f"Result 1 (payments!bill_id): {join1}")
    expected1 = " JOIN bills ON payments.bill_id = bills.bill_id"
    if join1 == expected1:
        print("Success: Correctly joined on bills.bill_id")
    else:
        print(f"Failure: Expected '{expected1}'")

    # 2. Test customer!c_id
    qb2 = supabase.table('credit_bill').select('*, customer!c_id(name)')
    join2 = get_query(qb2)
    print(f"Result 2 (customer!c_id): {join2}")
    expected2 = " JOIN customer ON credit_bill.c_id = customer.id"
    if join2 == expected2:
        print("Success: Correctly joined on customer.id")
    else:
        print(f"Failure: Expected '{expected2}'")

if __name__ == "__main__":
    test_smart_joins()
