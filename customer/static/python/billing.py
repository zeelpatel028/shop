from flask import render_template
from ... import customer_bp
from database.db import supabase
from datetime import datetime
import uuid

@customer_bp.route('/pending-bills')
def pending_bills():
    try:
        print("DEBUG: Fetching pending bills with manual Python inner-join...")
        # Fetch all unpaid credit bills
        bills_res = supabase.table('credit_bill').select('*').neq('payment_status', 'Paid').execute()
        raw_bills = bills_res.data or []
        print(f"DEBUG: Retrieved {len(raw_bills)} unpaid bills.")

        if not raw_bills:
            return render_template('pending_bills.html', customers=[], stats={'total_pending_amount': 0.0, 'total_pending_bills': 0})

        # Fetch all customers
        cust_res = supabase.table('customer').select('id, name, phone_no').execute()
        customers_list = cust_res.data or []
        
        # Build Customer Dictionary for fast lookup { c_id: { customer_data } }
        customer_map = { c['id']: c for c in customers_list }
        
        # Group by customer
        pending_data = {}
        for bill in raw_bills:
            c_id = bill.get('c_id')
            if not c_id:
                print(f"DEBUG: Skipping bill {bill.get('id')} due to missing c_id")
                continue
                
            cust = customer_map.get(c_id)
            if not cust:
                print(f"DEBUG: Skipping bill {bill.get('id')} because customer_id {c_id} does not exist in customer table.")
                continue

            if c_id not in pending_data:
                pending_data[c_id] = {
                    'customer_id': c_id,
                    'name': cust.get('name') or 'Unknown',
                    'phone': cust.get('phone_no') or '-',
                    'unpaid_amount': 0.0,
                    'bill_count': 0
                }
            
            # Safe float conversion to prevent float(None) TypeError
            rem_amt = bill.get('remaining_amount')
            pending_data[c_id]['unpaid_amount'] += float(rem_amt if rem_amt is not None else 0.0)
            pending_data[c_id]['bill_count'] += 1
            
        customers_pending = list(pending_data.values())
        
        # Summary stats for the view
        stats = {
            'total_pending_amount': sum(c['unpaid_amount'] for c in customers_pending),
            'total_pending_bills': sum(c['bill_count'] for c in customers_pending)
        }
    except Exception as e:
        import traceback
        print(f"ERROR fetching pending bills: {e}")
        traceback.print_exc()
        customers_pending = []
        stats = {'total_pending_amount': 0.0, 'total_pending_bills': 0}
        
    return render_template('pending_bills.html', customers=customers_pending, stats=stats)

@customer_bp.route('/api/unpaid-bills/<int:c_id>')
def get_customer_unpaid_bills(c_id):
    try:
        res = supabase.table('credit_bill').select('*').eq('c_id', c_id).neq('payment_status', 'Paid').execute()
        return {"status": "success", "bills": res.data or []}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@customer_bp.route('/approve-bills')
def approve_bills():
    try:
        print("DEBUG: Fetching approved (paid) bills with manual inner-join...")
        # Fetch all paid credit bills
        bills_res = supabase.table('credit_bill').select('*').eq('payment_status', 'Paid').execute()
        raw_bills = bills_res.data or []
        print(f"DEBUG: Retrieved {len(raw_bills)} paid bills.")

        if not raw_bills:
             return render_template('approve_bills.html', customers=[], stats={'total_approved_amount': 0.0, 'total_approved_bills': 0})
        
        # Fetch all customers
        cust_res = supabase.table('customer').select('id, name, phone_no').execute()
        customers_list = cust_res.data or []
        
        # Build Customer Dictionary for fast lookup { c_id: { customer_data } }
        customer_map = { c['id']: c for c in customers_list }

        # Group by customer
        approved_data = {}
        for bill in raw_bills:
            c_id = bill.get('c_id')
            if not c_id:
                print(f"DEBUG: Skipping paid bill {bill.get('id')} due to missing c_id")
                continue

            cust = customer_map.get(c_id)
            if not cust:
                print(f"DEBUG: Skipping paid bill {bill.get('id')} because customer_id {c_id} does not exist.")
                continue
                
            if c_id not in approved_data:
                approved_data[c_id] = {
                    'customer_id': c_id,
                    'name': cust.get('name') or 'Unknown',
                    'phone': cust.get('phone_no') or '-',
                    'total_paid': 0.0,
                    'bill_count': 0
                }
            
            # Safe float conversion to prevent float(None) TypeError
            paid_amt = bill.get('paid_amount')
            approved_data[c_id]['total_paid'] += float(paid_amt if paid_amt is not None else 0.0)
            approved_data[c_id]['bill_count'] += 1
            
        customers_approved = list(approved_data.values())
        
        # Summary stats for the view
        stats = {
            'total_approved_amount': sum(c['total_paid'] for c in customers_approved),
            'total_approved_bills': sum(c['bill_count'] for c in customers_approved)
        }
    except Exception as e:
        import traceback
        print(f"ERROR fetching approved bills: {e}")
        traceback.print_exc()
        customers_approved = []
        stats = {'total_approved_amount': 0.0, 'total_approved_bills': 0}
        
    return render_template('approve_bills.html', customers=customers_approved, stats=stats)

@customer_bp.route('/api/paid-bills/<int:c_id>')
def get_customer_paid_bills(c_id):
    try:
        res = supabase.table('credit_bill').select('*').eq('c_id', c_id).eq('payment_status', 'Paid').execute()
        return {"status": "success", "bills": res.data or []}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@customer_bp.route('/api/approve-bill/<int:bill_id>', methods=['POST'])
def approve_single_bill(bill_id):
    try:
        from flask import request
        data = request.json or {}
        payment_amount = float(data.get('amount', 0))

        if payment_amount <= 0:
            return {"status": "error", "message": "Invalid payment amount"}, 400

        # 1. Fetch the credit_bill to get linkage data
        cb_res = supabase.table('credit_bill').select('*').eq('id', bill_id).execute()
        if not cb_res.data:
            return {"status": "error", "message": "Credit bill record not found"}, 404
            
        cb_record = cb_res.data[0]
        main_bill_id = cb_record.get('bill_id')
        customer_id = cb_record.get('c_id')
        total_price = float(cb_record.get('total_price', 0))
        current_paid = float(cb_record.get('paid_amount', 0) or 0)
        
        new_paid = current_paid + payment_amount
        new_remaining = max(0, total_price - new_paid)
        
        # Determine status
        is_fully_paid = (new_remaining <= 0)
        new_payment_status = 'Paid' if is_fully_paid else 'Pending'
        new_bill_status = 'Completed' if is_fully_paid else 'Pending'

        # 2. Update credit_bill
        cb_update = {
            'payment_status': new_payment_status,
            'bill_status': new_bill_status,
            'paid_amount': new_paid,
            'remaining_amount': new_remaining,
            'approved_date': datetime.now().strftime("%Y-%m-%d"),
            'approved_time': datetime.now().strftime("%H:%M:%S"),
            'updated_at': datetime.now().isoformat()
        }
        supabase.table('credit_bill').update(cb_update).eq('id', bill_id).execute()
        
        # 3. Update main bills table (Sync with Ledger)
        if main_bill_id:
            bill_update = {
                'payment_status': new_payment_status,
                'bill_status': new_bill_status
            }
            supabase.table('bills').update(bill_update).eq('bill_id', main_bill_id).execute()
            
            # 4. Insert NEW payment record for history (Sync with Payments Dashboard)
            new_payment = {
                'bill_id': main_bill_id,
                'store_name': 'Main Store', # Credit bills usually from Main Store
                'payment_method': 'Cash', # Settlements are usually cash
                'payment_type': 'Partial' if not is_fully_paid else 'Full',
                'paid_amount': payment_amount,
                'remaining_amount': new_remaining,
                'payment_status': 'Paid', # This specific transaction is Paid
                'received_by': 'Counter',
                'payment_reference': f"SETTLE-{uuid.uuid4().hex[:10].upper()}",
                'transaction_id': f"SETTLE-{bill_id}-{uuid.uuid4().hex[:6].upper()}",
                'notes': f"Settlement payment for Credit Bill #{bill_id}",
                'is_bill_generated': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            supabase.table('payments').insert(new_payment).execute()
            
            # Also update any previous 'Pending' records for this bill to reflect new remaining
            supabase.table('payments').update({'remaining_amount': new_remaining, 'updated_at': datetime.now().isoformat()}).eq('bill_id', main_bill_id).eq('payment_status', 'Pending').execute()
            
        # 5. Update customer stats
        if customer_id:
            cust_res = supabase.table('customer').select('*').eq('id', customer_id).execute()
            if cust_res.data:
                cust = cust_res.data[0]
                
                current_total_invested = float(cust.get('padin_amount_total', 0) or 0)
                
                update_data = {
                    "padin_amount_last": payment_amount,
                    "padin_amount_total": current_total_invested + payment_amount,
                    "last_payment_date": datetime.now().isoformat()
                }

                # Only decrement pending count if fully paid
                if is_fully_paid:
                    current_pending = int(cust.get('panding_bill_count', 0) or 0)
                    update_data["panding_bill_count"] = max(0, current_pending - 1)
                
                supabase.table('customer').update(update_data).eq('id', customer_id).execute()
        
        msg = "Bill fully paid and settled." if is_fully_paid else f"Partial payment of ₹{payment_amount} accepted. Remaining: ₹{new_remaining}"
        return {"status": "success", "message": msg}, 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}, 500
