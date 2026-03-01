from database.db import supabase
from datetime import datetime
import uuid

def test_integrity():
    print("Testing Data Integrity for Bills and Payments...")
    
    # 1. Test Mock Bill Insertion
    print("\nSimulating Bill Creation (Cash)...")
    bill_no = f"TEST-CASH-{uuid.uuid4().hex[:6].upper()}"
    new_bill = {
        "bill_no": bill_no,
        "store_name": "Main Store",
        "total_product": 1,
        "total_quantity": 1,
        "subtotal_amount": 100.0,
        "total_tax_amount": 18.0,
        "bill_total": 118.0,
        "payment_status": "Paid",
        "bill_status": "Completed",
        "payment_method": "Cash",
        "customer_name": "Test User",
        "customer_phone": "1234567890"
    }
    
    bill_res = supabase.table('bills').insert(new_bill).execute()
    if not bill_res.data:
        print("FAIL: Bill insertion failed")
        return
    
    bill_pk = bill_res.data[0]['bill_id']
    print(f"SUCCESS: Bill created with ID {bill_pk}")

    # 2. Test Payment Record for Bill
    print("\nSimulating Payment Record...")
    new_payment = {
        "bill_id": bill_pk,
        "store_name": "Main Store",
        "payment_method": "Cash",
        "payment_type": "Full",
        "paid_amount": 118.0,
        "remaining_amount": 0,
        "payment_status": "Paid",
        "received_by": "Counter",
        "payment_reference": f"TEST-REF-{uuid.uuid4().hex[:6].upper()}",
        "transaction_id": f"TEST-TX-{uuid.uuid4().hex[:6].upper()}",
        "is_bill_generated": True,
        "notes": "Test payment record"
    }
    
    pay_res = supabase.table('payments').insert(new_payment).execute()
    if pay_res.data:
        print(f"SUCCESS: Payment record created for Bill {bill_pk}")
    else:
        print("FAIL: Payment insertion failed")

    # 3. Test Credit Bill Settlement (New History Model)
    print("\nSimulating Credit Bill Settlement Transaction...")
    settle_payment = {
        'bill_id': bill_pk,
        'store_name': 'Main Store',
        'payment_method': 'Cash',
        'payment_type': 'Partial',
        'paid_amount': 50.0,
        'remaining_amount': 68.0,
        'payment_status': 'Paid',
        'received_by': 'Counter',
        'payment_reference': f"SETTLE-TEST-{uuid.uuid4().hex[:6].upper()}",
        'transaction_id': f"SETTLE-TX-{uuid.uuid4().hex[:6].upper()}",
        'notes': "Test settlement transaction",
        'is_bill_generated': True
    }
    
    settle_res = supabase.table('payments').insert(settle_payment).execute()
    if settle_res.data:
        print("SUCCESS: Settlement transaction history record created.")
    else:
        print("FAIL: Settlement transaction insertion failed")

    print("\nIntegrity tests completed. Please check your Supabase dashboard or use 'payments' view to verify results.")

if __name__ == "__main__":
    test_integrity()
