import os
import sys
# Add parent directory to path so database.db can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database.db import supabase
    c_id = 1
    # Check existing data
    existing = supabase.table('customer').select('*').eq('id', c_id).execute()
    print("Existing:", existing.data)
    
    # Try updating
    data = {"name": existing.data[0]["name"] + " edited"}
    res = supabase.table('customer').update(data).eq('id', c_id).execute()
    print("Update Response:", res.data)

    # Revert
    supabase.table('customer').update({"name": existing.data[0]["name"]}).eq('id', c_id).execute()
    print("Reverted.")
except Exception as e:
    import traceback
    traceback.print_exc()
