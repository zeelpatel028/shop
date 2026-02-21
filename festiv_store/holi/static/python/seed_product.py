import sys
import os
from datetime import datetime

# Add project root to sys.path to allow imports from database package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from database.db import supabase

def seed_product():
    print("Attempting to insert a test product with auto-increment...")
    try:
        # 1. Logic matching routes.py (no manual ID)
        cost_price = 80.0
        base_price = 100.0
        tax_percent = 5.0
        stock_qty = 50

        tax_amount = (base_price * tax_percent) / 100
        sell_price = base_price + tax_amount
        
        # New formula: Profit Margin = Sell Price - Cost Price
        profit_margin = sell_price - cost_price

        test_product = {
            "store_name": "Test Script Vendor",
            "product_name": "Auto-Increment Product",
            "brand": "ScriptBrand",
            "category": "Colors",
            "price_quantity": "1",
            "product_unit": "kg",
            "cost_price": 80.0,
            "base_price": base_price,
            "tax_percent": tax_percent,
            "tax_amount": tax_amount,
            "profit_margin": profit_margin,
            "sell_price": sell_price,
            "stock": stock_qty,
            "sold_stock": 0,
            "stock_status": "In Stock",
            "product_status": "Active",
            "last_updated_quantity": stock_qty,
            "created_at": datetime.now().isoformat()
        }

        # 2. Insert into Supabase (DB will generate product_id)
        data = supabase.table('products').insert(test_product).execute()
        print("Product inserted successfully!")
        print("Inserted Data:", data.data)

    except Exception as e:
        import traceback
        print(f"Error seeding product: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    seed_product()
