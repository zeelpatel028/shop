import sys
import os

# Add project root to sys.path to allow imports from database package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from database.db import supabase

def seed_product():
    print("Attempting to insert a test product...")
    try:
        # 1. Calculate new ID (Manual ID logic as per routes.py)
        # Check if any products exist to get max ID
        products_response = supabase.table('products').select('id').order('id', desc=True).limit(1).execute()
        if products_response.data:
            new_id = products_response.data[0]['id'] + 1
        else:
            new_id = 1
        
        print(f"Generated new ID: {new_id}")

        # 2. Define Product Data
        test_product = {
            "id": new_id,
            "product_name": "Python Script Test Product",
            "name": "Python Script Test Product", # Legacy
            "product_category": "Colors",
            "category": "Colors", # Legacy
            "store_name": "Test Script Vendor",
            "product_brand": "ScriptBrand",
            "base_price": 100.00,
            "price": 100.00, # Legacy
            "offer_price": 90.00,
            "stock": 50,
            "product_weight": 0.5,
            "product_unit": "kg",
            "tax_percent": 5.0,
            "tax_amount": 5.0,
            "final_price": 105.0, # base + tax
            "image": "Holi colours.jpg",
            "product_status": "Active",
            "stock_status": "InStock"
        }

        # 3. Insert into Supabase
        data = supabase.table('products').insert(test_product).execute()
        print("Product inserted successfully!")
        print("Inserted Data:", data.data)

    except Exception as e:
        print(f"Error seeding product: {e}")

def add_product_logic(product_data):
    """
    Logic extracted from routes.py for adding a product.
    Expects product_data to be a dictionary matching the form fields.
    """
    try:
        # Auto-increment logic
        products_response = supabase.table('products').select('id').order('id', desc=True).limit(1).execute()
        if products_response.data:
            new_id = products_response.data[0]['id'] + 1
        else:
            new_id = 1

        # Extract data (simulating request.form.get)
        stock_qty = int(product_data.get('stock', 0))
        base_price = float(product_data.get('base_price', 0))
        offer_price = float(product_data.get('offer_price', 0)) if product_data.get('offer_price') else None
        cost_price = float(product_data.get('cost_price', 0)) if product_data.get('cost_price') else None
        tax_percent = float(product_data.get('tax_percent', 0)) if product_data.get('tax_percent') else 0
        
        tax_amount = (base_price * tax_percent) / 100
        final_price = base_price + tax_amount
        if offer_price:
             final_price = offer_price

        new_product = {
            "id": new_id,
            "product_name": product_data.get('product_name'),
            "name": product_data.get('product_name'),
            "product_category": product_data.get('product_category'),
            "category": product_data.get('product_category'),
            
            "store_name": product_data.get('store_name'),
            "product_brand": product_data.get('product_brand'),
            
            "base_price": base_price,
            "price": base_price,
            "offer_price": offer_price,
            "cost_price": cost_price,
            "tax_percent": tax_percent,
            "tax_amount": tax_amount,
            "final_price": final_price,
            
            "stock": stock_qty,
            "product_weight": float(product_data.get('product_weight', 0)) if product_data.get('product_weight') else None,
            "product_unit": product_data.get('product_unit'),
            
            "product_quantity": int(product_data.get('product_quantity', 1)) if product_data.get('product_quantity') else None,
            "price_quantity": product_data.get('price_quantity'),
            "profit_margin": float(product_data.get('profit_margin', 0)) if product_data.get('profit_margin') else None,
            
            "image": "Holi colours.jpg",
            
            "product_status": product_data.get('product_status'),
            "stock_status": "InStock" if stock_qty > 0 else "OutOfStock"
        }
        data = supabase.table('products').insert(new_product).execute()
        print("Product added successfully via logic function!")
        return data.data
    except Exception as e:
         print(f"Error in add_product_logic: {e}")
         return None

if __name__ == "__main__":
    seed_product()
