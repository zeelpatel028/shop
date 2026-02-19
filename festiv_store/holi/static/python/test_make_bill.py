import requests
import json
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from database.db import supabase

def make_bill_logic(items, customer_name=None, customer_phone=None):
    """
    Logic extracted from routes.py for making a bill.
    """
    try:
        if not items:
            return {'success': False, 'message': 'No items in cart'}

        # Calculate Totals
        total_items = len(items)
        total_quantity = sum(item['quantity'] for item in items)
        
        # Recalculate amounts on backend for security
        subtotal_amount = 0
        total_tax_amount = 0
        bill_total = 0
        
        # Validate Stock & Calculate
        for item in items:
            # Ideally fetch fresh product data here to verify stock and price
            # For this implementation, we'll verify stock at least
            prod_data = supabase.table('products').select('stock').eq('id', item['id']).single().execute()
            current_stock = prod_data.data['stock']
            
            if current_stock < item['quantity']:
                 return {'success': False, 'message': f"Insufficient stock for {item['name']}"}
            
            # Calculation (using frontend sent prices for now, but in production should use DB prices)
            final_price = item['final_price']
            qty = item['quantity']
            tax_percent = item['tax_percent']
            
            line_total = final_price * qty
            bill_total += line_total
            
            # Back-calculate base and tax
            base_total = line_total / (1 + (tax_percent/100))
            subtotal_amount += base_total
            tax_amount = line_total - base_total
            total_tax_amount += tax_amount

        # Generate Bill ID/No
        # Get max ID
        try:
            bills_resp = supabase.table('bills').select('id').order('id', desc=True).limit(1).execute()
            new_id = bills_resp.data[0]['id'] + 1 if bills_resp.data else 1
        except:
            new_id = 1
            
        bill_no = f"BILL{new_id:04d}"
        
        from datetime import datetime
        now = datetime.now()
        
        new_bill = {
            "id": new_id,
            "bill_no": bill_no,
            "store_name": "Holi Hub", # Default
            "total_items": total_items,
            "total_quantity": total_quantity,
            "subtotal_amount": round(subtotal_amount, 2),
            "total_tax_amount": round(total_tax_amount, 2),
            "bill_total": round(bill_total, 2),
            "total": round(bill_total, 2), # Legacy support
            "date": now.strftime("%Y-%m-%d"),
            "bill_date": now.strftime("%Y-%m-%d"),
            "bill_time": now.strftime("%H:%M:%S"),
            "payment_status": "Paid", # Default to paid for now
            "bill_status": "Completed"
        }
        
        # Insert Bill
        bill_insert_response = supabase.table('bills').insert(new_bill).execute()
        
        # Get the generated serial bill_id
        if bill_insert_response.data:
            bill_pk = bill_insert_response.data[0]['bill_id']
        else:
             # Fallback if for some reason data isn't returned
             saved_bill = supabase.table('bills').select('bill_id').eq('id', new_id).single().execute()
             bill_pk = saved_bill.data['bill_id']
        
        # Insert Bill Items & Update Stock
        for item in items:
            # Bill Item
            line_total = item['final_price'] * item['quantity']
            
            bill_item = {
                "bill_id": bill_pk, 
                "product_id": item['id'], 
                "product_name": item['name'],
                "quantity": item['quantity'],
                "final_price": item['final_price'],
                "total_price": line_total,
                "tax_percent": item['tax_percent']
            }
            
            # Insert Item
            supabase.table('bill_items').insert(bill_item).execute()
            
            # Update Stock
            new_stock = item['stock'] - item['quantity']
            supabase.table('products').update({'stock': new_stock}).eq('id', item['id']).execute()

        return {'success': True, 'bill_no': bill_no}

    except Exception as e:
        print(f"Error making bill: {e}")
        return {'success': False, 'message': str(e)}

def test_make_bill():
    print("Testing Make Bill Endpoint...")
    
    # Using known product ID from previous step (ID: 1)
    product_id = 1
    print(f"Using Product ID: {product_id}")
    
    # 2. Prepare Payload
    payload = {
        "customer_name": "Test Customer",
        "customer_phone": "1234567890",
        "items": [
            {
                "id": product_id,
                "name": "Python Script Test Product",
                "price": 100.0,
                "final_price": 105.0,
                "tax_percent": 5.0,
                "quantity": 1,
                "stock": 50 # Mock stock
            }
        ]
    }
    
    # 3. Send POST request
    url = 'http://127.0.0.1:5000/festiv_store/holi/make-bill'
    
    try:
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"Bill created successfully! Bill No: {data.get('bill_no')}")
            else:
                print(f"Failed: {data.get('message')}")
        else:
            print("Failed to create bill via API.")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_make_bill()
