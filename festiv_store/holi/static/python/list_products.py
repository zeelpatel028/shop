import sys
import os
# Add project root to path (4 levels up from this script location)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from database.db import supabase

try:
    response = supabase.table('products').select('*').execute()
    print("Products in DB:")
    for p in response.data:
        print(f"Item: {p}")
        for k, v in p.items():
            print(f"  {k}: {type(v)}")
        break # Only check first item
except Exception as e:
    print(f"Error: {e}")
