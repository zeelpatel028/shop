from flask import render_template, request, redirect, url_for, flash
from ... import customer_bp
from database.db import supabase

@customer_bp.route('/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        try:
            # 1. Mandatory Data Extraction (Personal Information)
            name = request.form.get('name', '').strip()
            phone_no = request.form.get('phone_no', '').strip()
            address = request.form.get('address', '').strip()
            
            # 2. Strong Validation Logic
            errors = []
            if not name:
                errors.append("Full Name is required.")
            elif len(name) < 3:
                errors.append("Name must be at least 3 characters long.")
                
            if not phone_no:
                errors.append("Phone Number is required.")
            elif not phone_no.isdigit() or len(phone_no) < 10:
                errors.append("Please enter a valid 10-digit phone number.")
                
            if not address:
                errors.append("Address is required.")

            # 3. Handle Validation Failures
            if errors:
                for error in errors:
                    flash(error, "danger")
                return render_template('add_customer.html', form_data=request.form)

            # 4. Process Optional Data (Billing/Classification)
            # These are optional as requested - if empty, they default to 0 or 'Active'
            data = {
                'name': name,
                'phone_no': phone_no,
                'address': address,
                'padin_amount_last': float(request.form.get('padin_amount_last') or 0),
                'padin_amount_total': float(request.form.get('padin_amount_total') or 0),
                'panding_bill_count': int(request.form.get('panding_bill_count') or 0),
                'all_bill_count': int(request.form.get('all_bill_count') or 0),
                'status': request.form.get('status', 'Active'),
                'created_by': request.form.get('created_by', 'System')
            }
            
            # 5. Database Operation
            res = supabase.table('customer').insert(data).execute()
            
            if res.data:
                flash(f"Customer '{name}' registered successfully!", "success")
                return redirect(url_for('customer.all_customers'))
            else:
                flash("Database Error: Could not save customer. Possible duplicate phone number.", "danger")
                
        except Exception as e:
            print(f"Error adding customer: {e}")
            flash("A system error occurred. Please try again later.", "danger")
            
    return render_template('add_customer.html')

@customer_bp.route('/edit/<int:c_id>', methods=['POST'])
def edit_customer(c_id):
    try:
        # 1. Mandatory Data Extraction
        name = request.form.get('name', '').strip()
        phone_no = request.form.get('phone_no', '').strip()
        address = request.form.get('address', '').strip()
        
        # 2. Strong Validation Logic (Same as Add)
        errors = []
        if not name:
            errors.append("Full Name is required.")
        elif len(name) < 3:
            errors.append("Name must be at least 3 characters long.")
            
        if not phone_no:
            errors.append("Phone Number is required.")
        elif not phone_no.isdigit() or len(phone_no) < 10:
            errors.append("Please enter a valid 10-digit phone number.")
            
        if not address:
            errors.append("Address is required.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return redirect(url_for('customer.all_customers'))

        # 3. Process All Data
        data = {
            'name': name,
            'phone_no': phone_no,
            'address': address,
            'padin_amount_last': float(request.form.get('padin_amount_last') or 0),
            'padin_amount_total': float(request.form.get('padin_amount_total') or 0),
            'panding_bill_count': int(request.form.get('panding_bill_count') or 0),
            'all_bill_count': int(request.form.get('all_bill_count') or 0),
            'status': request.form.get('status', 'Active'),
            'created_by': request.form.get('created_by', 'System')
        }
        
        # 4. Database Operation
        res = supabase.table('customer').update(data).eq('id', c_id).execute()
        
        if res.data:
            flash(f"Customer '{name}' updated successfully!", "success")
        else:
            flash("Database Error: Could not update customer.", "danger")
            
    except Exception as e:
        print(f"Error editing customer: {e}")
        flash("A system error occurred during update.", "danger")
        
    return redirect(url_for('customer.all_customers'))

@customer_bp.route('/all')
def all_customers():
    try:
        res = supabase.table('customer').select('*').execute()
        customers = res.data or []
        
        # Calculate stats in backend to keep template clean
        total_customers = len(customers)
        active_users = sum(1 for c in customers if c.get('status') == 'Active')
        credit_active = sum(1 for c in customers if int(c.get('panding_bill_count') or 0) > 0)
        
        stats = {
            'total_customers': total_customers,
            'active_users': active_users,
            'credit_active': credit_active
        }
    except Exception as e:
        print(f"Error fetching customers: {e}")
        customers = []
        stats = {'total_customers': 0, 'active_users': 0, 'credit_active': 0}
        
    return render_template('all_customers.html', customers=customers, stats=stats)
