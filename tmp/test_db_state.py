import os
import sys
# Add parent directory to path so database.db can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from database.db import supabase
    c_id = 1
    existing = supabase.table('customer').select('*').eq('id', c_id).execute()
    print("Database State after POST:", existing.data[0]['name'])
    
    # Revert
    supabase.table('customer').update({"name": "Zeel Dobariya"}).eq('id', c_id).execute()
except Exception as e:
    import traceback
    traceback.print_exc()
