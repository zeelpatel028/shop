import uuid
import random
import string
import hashlib
from datetime import datetime, timedelta

class PaymentService:
    SECRET_KEY = "MAIN-STORE-SECURE-SALT" # In production, move to env var

    @staticmethod
    def generate_secure_reference():
        """
        Generates a secure payment reference: MAIN-{timestamp}-{random6}
        Plus a short hash for verification to prevent tampering.
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        base_ref = f"MAIN-{timestamp}-{random_str}"
        
        # Add a 6-char hash suffix for integrity
        signature = hashlib.sha256(f"{base_ref}{PaymentService.SECRET_KEY}".encode()).hexdigest()[:6].upper()
        return f"{base_ref}-{signature}"

    @staticmethod
    def verify_reference_integrity(reference):
        """
        Verifies if the reference has been tampered with using the hash suffix.
        """
        if not reference or '-' not in reference:
            return False
        
        parts = reference.split('-')
        if len(parts) < 4: # MAIN-TIMESTAMP-RANDOM-HASH
            return False
            
        signature = parts[-1]
        base_ref = "-".join(parts[:-1])
        
        expected_signature = hashlib.sha256(f"{base_ref}{PaymentService.SECRET_KEY}".encode()).hexdigest()[:6].upper()
        return signature == expected_signature

    @staticmethod
    def generate_upi_url(amount, payment_ref):
        """
        Generates a UPI URL for the given amount and reference.
        """
        upi_id = "zeelptl028@okaxis"
        name = "Main Store"
        # We use payment_ref in the transaction note (tn) to track the payment
        url = f"upi://pay?pa={upi_id}&pn={name}&am={amount:.2f}&tn={payment_ref}&cu=INR"
        return url

    @staticmethod
    def cleanup_expired_payments(supabase):
        """
        Marks all pending payments that have passed their expiry time as Expired.
        Automates DB hygiene.
        """
        now = datetime.now().isoformat()
        try:
            supabase.table('payments')\
                .update({'payment_status': 'Failed', 'updated_at': now})\
                .eq('payment_status', 'Pending')\
                .lt('payment_expire_at', now)\
                .execute()
        except Exception as e:
            print(f"DEBUG: Cleanup failed: {e}")

    @staticmethod
    def create_pending_payment(supabase, payment_data):
        """
        Inserts a pending payment record into Supabase with 5-minute expiry.
        Also triggers cleanup of old payments.
        """
        # Auto-cleanup on every new payment preparation
        PaymentService.cleanup_expired_payments(supabase)

        now = datetime.now()
        expiry = now + timedelta(minutes=5)
        
        # Set defaults to avoid NULLs
        payment_data.setdefault('store_name', 'Main Store')
        payment_data.setdefault('payment_type', 'Full')
        payment_data.setdefault('remaining_amount', 0.0)
        payment_data.setdefault('received_by', 'Counter')
        payment_data.setdefault('payment_status', 'Pending')
        payment_data.setdefault('is_bill_generated', False)
        
        payment_data['created_at'] = now.isoformat()
        payment_data['updated_at'] = now.isoformat()
        payment_data['payment_expire_at'] = expiry.isoformat()
        
        resp = supabase.table('payments').insert(payment_data).execute()
        return resp.data[0] if resp.data else None

    @staticmethod
    def check_status(supabase, payment_reference):
        """
        Checks the status of a payment by its reference ID, handling expiry.
        """
        if not PaymentService.verify_reference_integrity(payment_reference):
            return 'Invalid'

        resp = supabase.table('payments').select('payment_status, payment_expire_at').eq('payment_reference', payment_reference).execute()
        
        if not resp.data:
            return 'Not Found'
            
        record = resp.data[0]
        status = record.get('payment_status', 'Pending')
        expire_at_str = record.get('payment_expire_at')
        
        if status == 'Pending' and expire_at_str:
            expire_at = datetime.fromisoformat(expire_at_str)
            if datetime.now() > expire_at:
                # Mark as failed in DB to satisfy check constraint
                supabase.table('payments').update({
                    'payment_status': 'Failed',
                    'updated_at': datetime.now().isoformat()
                }).eq('payment_reference', payment_reference).execute()
                return 'Expired'
                
        return status

    @staticmethod
    def mark_as_paid(supabase, payment_reference, upi_txn_id=None, bill_id=None):
        """
        Updates a payment status to Paid and links bill_id/txn_id.
        Strict verification: must be pending and not expired.
        """
        if not PaymentService.verify_reference_integrity(payment_reference):
            print(f"DEBUG mark_as_paid: integrity check failed for {payment_reference}")
            return False

        # Check current status
        status = PaymentService.check_status(supabase, payment_reference)
        print(f"DEBUG mark_as_paid: check_status returned {status}")
        if status != 'Pending':
            print(f"DEBUG mark_as_paid: status is {status}, not Pending")
            return False

        # Fetch current record for paid_amount
        res = supabase.table('payments').select('paid_amount').eq('payment_reference', payment_reference).execute()
        if not res.data:
            print(f"DEBUG mark_as_paid: DB returned no data for {payment_reference}")
            return False
            
        amount = res.data[0].get('paid_amount', 0)

        update_data = {
            'payment_status': 'Paid',
            'updated_at': datetime.now().isoformat(),
            'paid_amount': amount
        }
        
        if upi_txn_id:
            update_data['transaction_id'] = upi_txn_id
        
        if bill_id:
            update_data['bill_id'] = bill_id
            
        resp = supabase.table('payments').update(update_data).eq('payment_reference', payment_reference).execute()
        return bool(resp.data)

    @staticmethod
    def mark_bill_as_generated(supabase, payment_reference):
        """
        Marks the payment record as having a bill generated.
        """
        resp = supabase.table('payments').update({'is_bill_generated': True}).eq('payment_reference', payment_reference).execute()
        return bool(resp.data)

    @staticmethod
    def is_bill_already_generated(supabase, payment_reference):
        """
        Checks if a bill has already been generated for this payment reference.
        """
        try:
            resp = supabase.table('payments').select('is_bill_generated').eq('payment_reference', payment_reference).execute()
            if resp.data:
                return resp.data[0].get('is_bill_generated', False)
        except Exception as e:
            print(f"DEBUG: Schema check failed (likely missing column): {e}")
            return False
        return False
