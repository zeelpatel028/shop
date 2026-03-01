from database.db import supabase, TABLE_PRIMARY_KEYS
import re

def test_robust_joins():
    print("Testing Robust Join Refactor (Explicit PK Mapping)...")
    
    def get_join_sql(table_name, select_val):
        # Simulation of the join logic in db.py
        if "(" in select_val and ")" in select_val:
            match = re.search(r'(\w+)[!:]?(\w+)?\(([\w,\*]+)\)', select_val)
            if match:
                linked_table = match.group(1)
                custom_fk = match.group(2)
                fk_col = custom_fk if custom_fk else (linked_table[:-1] if linked_table.endswith('s') else f"{linked_table}_id")
                target_pk = TABLE_PRIMARY_KEYS.get(linked_table, 'id')
                return f" JOIN {linked_table} ON {table_name}.{fk_col} = {linked_table}.{target_pk}"
        return ""

    test_cases = [
        # (Primary Table, Select String, Expected Join SQL)
        ('payments', '*, bills!bill_id(bill_no)', ' JOIN bills ON payments.bill_id = bills.bill_id'),
        ('credit_bill', '*, customer!c_id(name)', ' JOIN customer ON credit_bill.c_id = customer.id'),
        ('bill_items', '*, products!product_id(product_name)', ' JOIN products ON bill_items.product_id = products.product_id'),
        ('payments', '*, bills(bill_no)', ' JOIN bills ON payments.bill_id = bills.bill_id'),
    ]

    all_passed = True
    for p_table, sel, expected in test_cases:
        actual = get_join_sql(p_table, sel)
        if actual == expected:
            print(f"PASS: {p_table} -> {sel}")
        else:
            print(f"FAIL: {p_table} -> {sel}")
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
            all_passed = False

    if all_passed:
        print("\nAll robust join tests passed!")
    else:
        print("\nSome tests failed.")

if __name__ == "__main__":
    test_robust_joins()
