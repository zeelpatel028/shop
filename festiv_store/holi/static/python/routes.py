from datetime import datetime
import json
import uuid
import os
from .payment_service import PaymentService
from collections import defaultdict
from flask import render_template, request, redirect, url_for, flash, jsonify
from .... import festiv_store_bp
from database.db import supabase
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def safe_float(value, default=0.0):
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default

def generate_bill_pdf(bill_data, items):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # Define custom styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, alignment=1, spaceAfter=2, textColor=colors.black)
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontSize=12, alignment=1, spaceAfter=10)
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=9)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')

    # Header
    elements.append(Paragraph("<b>BIG TULSHI SHOP</b>", title_style))
    elements.append(Paragraph("HOLI STORE", subtitle_style))
    
    # Tax Invoice Label
    elements.append(Paragraph("<b>TAX INVOICE</b>", ParagraphStyle('TaxStyle', parent=styles['Normal'], fontSize=12, alignment=1)))
    elements.append(Paragraph("Original", ParagraphStyle('OriginalStyle', parent=styles['Normal'], fontSize=8, alignment=1, spaceAfter=10)))
    
    elements.append(Spacer(1, 0.1 * inch))

    # Bill Info & Customer Info Table
    info_data = [
        [Paragraph(f"<b>Bill No:</b> {bill_data['bill_no']}", info_style), Paragraph(f"<b>Customer:</b> {bill_data['customer_name'] or 'Cash'}", info_style)],
        [Paragraph(f"<b>Date:</b> {bill_data['bill_date']} {bill_data['bill_time']}", info_style), Paragraph(f"<b>Phone:</b> {bill_data['customer_phone'] or '-'}", info_style)],
        [Paragraph(f"<b>Payment:</b> {bill_data['payment_method']}", info_style), ""]
    ]
    info_table = Table(info_data, colWidths=[3 * inch, 3.5 * inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Items Table Header
    table_data = [['Sr', 'Description', 'HSN', 'Qty', 'Rate', 'Taxable', 'CGST', 'SGST', 'Amount']]
    
    # Items
    for i, item in enumerate(items, 1):
        # Calculate CGST/SGST (splitting the tax amount by 2)
        tax_amt = safe_float(item.get('tax_amount', 0))
        cgst_sgst_amt = tax_amt / 2
        tax_pct = safe_float(item.get('tax_percent', 0))
        cgst_sgst_pct = tax_pct / 2
        
        row = [
            str(i),
            Paragraph(f"{item['name']}", info_style),
            "0910", # Placeholder HSN
            str(item['quantity']),
            f"{item['final_price']:.2f}",
            f"{item['base_price']:.2f}",
            f"{cgst_sgst_amt:.2f}",
            f"{cgst_sgst_amt:.2f}",
            f"{item['line_total']:.2f}"
        ]
        table_data.append(row)

    # Empty rows to fill space if needed (optional)
    # for _ in range(max(0, 10 - len(items))):
    #     table_data.append(["", "", "", "", "", "", "", "", ""])

    # Table Styles
    items_table = Table(table_data, colWidths=[0.3*inch, 2.2*inch, 0.6*inch, 0.5*inch, 0.7*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.8*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'), # Description left aligned
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Totals Section
    totals_data = [
        ['', '', '', '', '', 'Taxable Amt', f"{bill_data['subtotal_amount']:.2f}"],
        ['', '', '', '', '', 'CGST Amt', f"{(bill_data['total_tax_amount']/2):.2f}"],
        ['', '', '', '', '', 'SGST Amt', f"{(bill_data['total_tax_amount']/2):.2f}"],
        ['', '', '', '', '', Paragraph('<b>Grand Total</b>', header_style), Paragraph(f"<b>₹{bill_data['bill_total']:.2f}</b>", header_style)]
    ]
    
    totals_table = Table(totals_data, colWidths=[0.3*inch, 2.2*inch, 0.6*inch, 0.5*inch, 0.7*inch, 1.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (-2, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (-2, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(totals_table)
    
    elements.append(Spacer(1, 0.5 * inch))
    
    # Footer
    footer_text = "Certified that particulars given above are true and correct."
    elements.append(Paragraph(footer_text, info_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    elements.append(Paragraph(f"For, <b>BIG TULSHI SHOP</b>", ParagraphStyle('FooterStyle', parent=styles['Normal'], fontSize=10, alignment=2)))
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

@festiv_store_bp.route('/holi')
def holi_dashboard():
    # Count documents using Supabase
    try:
        product_count = supabase.table('products').select('*', count='exact').execute().count
        bill_count = supabase.table('bills').select('*', count='exact').execute().count
        
        # Fetching all bills for revenue calculation:
        bills_response = supabase.table('bills').select('*').order('created_at', desc=True).execute()
        all_bills = bills_response.data or []
        total_revenue = sum(safe_float(bill.get('bill_total')) for bill in all_bills)

        # CALCULATE TOTAL PROFIT:
        items_res = supabase.table('bill_items').select('product_id, product_name, quantity').execute()
        bill_items = items_res.data or []
        
        prods_res = supabase.table('products').select('product_id, product_name, profit_margin, stock, sell_price').execute()
        all_products = prods_res.data or []
        product_profits = {p['product_id']: safe_float(p.get('profit_margin')) for p in all_products}
        
        total_profit = 0
        for item in bill_items:
            p_id = item.get('product_id')
            qty = safe_float(item.get('quantity'))
            margin = product_profits.get(p_id, 0)
            total_profit += (qty * margin)

        # --- ENHANCED DASHBOARD DATA ---
        
        # Average order value
        avg_order = total_revenue / bill_count if bill_count else 0
        
        # Today's stats
        from datetime import timedelta
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        today_bills = [b for b in all_bills if (b.get('created_at') or '') >= today_start]
        today_revenue = sum(safe_float(b.get('bill_total')) for b in today_bills)
        today_count = len(today_bills)
        
        # Recent 5 bills for activity feed
        recent_bills = all_bills[:5]
        
        # Top selling products (by quantity sold)
        from collections import Counter
        product_sales = Counter()
        for item in bill_items:
            pname = item.get('product_name', 'Unknown')
            product_sales[pname] += safe_float(item.get('quantity'))
        top_products = product_sales.most_common(5)
        
        # Low stock alerts
        low_stock = [p for p in all_products if safe_float(p.get('stock')) <= 10.0]
        
        # Profit margin percentage
        profit_pct = (total_profit / total_revenue * 100) if total_revenue else 0

    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        product_count = 0
        bill_count = 0
        total_revenue = 0
        total_profit = 0
        avg_order = 0
        today_revenue = 0
        today_count = 0
        recent_bills = []
        top_products = []
        low_stock = []
        profit_pct = 0
    
    return render_template('holi.html', 
                         product_count=product_count, 
                         bill_count=bill_count, 
                         revenue=total_revenue,
                         total_profit=total_profit,
                         avg_order=avg_order,
                         today_revenue=today_revenue,
                         today_count=today_count,
                         recent_bills=recent_bills,
                         top_products=top_products,
                         low_stock=low_stock,
                         profit_pct=profit_pct)

@festiv_store_bp.route('/holi/master-stock')
def master_stock():
    try:
        products_response = supabase.table('products').select('*').execute()
        all_products = products_response.data or []
        
        # Fetch bill_items for sales count
        items_response = supabase.table('bill_items').select('product_name, quantity').execute()
        bill_items = items_response.data or []
    except Exception as e:
        print(f"Error fetching master stock data: {e}")
        all_products = []
        bill_items = []
    
    # Calculate sales count
    product_sales = defaultdict(int)
    for item in bill_items:
        if 'product_name' in item and item['product_name']:
            product_sales[item['product_name']] += item.get('quantity', 0)
        
    # Attach sales to products
    for p in all_products:
        p['sales'] = product_sales.get(p.get('product_name'), 0)
        
    # Filter products
    active_products = [p for p in all_products if p.get('product_status', 'Active') == 'Active']
    inactive_products = [p for p in all_products if p.get('product_status') == 'Inactive']
        
    most_sold = sorted(active_products, key=lambda x: x.get('sales', 0), reverse=True)
    low_stock = [p for p in active_products if p.get('stock', 0) <= 10]
    
    return render_template('master_stock.html', 
                         products=active_products, 
                         inactive_products=inactive_products,
                         most_sold=most_sold,
                         low_stock=low_stock)

@festiv_store_bp.route('/holi/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        # 1. Check if product has any sales (bill_items)
        items_check = supabase.table('bill_items').select('bill_item_id').eq('product_id', product_id).limit(1).execute()
        
        if items_check.data:
            # 2. Has sales: Soft delete (Deactivate)
            supabase.table('products').update({'product_status': 'Inactive', 'stock_status': 'Out of Stock'}).eq('product_id', product_id).execute()
            flash('Product moved to Removed list (preserves sales history).', 'info')
        else:
            # 3. No sales: Hard delete
            response = supabase.table('products').delete().eq('product_id', product_id).execute()
            if response.data:
                flash('Product deleted successfully!', 'success')
            else:
                flash('Product not found or could not be deleted!', 'warning')
            
    except Exception as e:
        print(f"DEBUG: Error in smart delete: {e}")
        flash(f'Error processing deletion: {str(e)}', 'error')
        
    return redirect(url_for('festiv_store.master_stock'))

@festiv_store_bp.route('/holi/restore-product/<int:product_id>', methods=['POST'])
def restore_product(product_id):
    try:
        # Restore product to Active status
        supabase.table('products').update({'product_status': 'Active', 'stock_status': 'In Stock'}).eq('product_id', product_id).execute()
        flash('Product restored successfully!', 'success')
    except Exception as e:
        print(f"Error restoring product: {e}")
        flash('Error restoring product!', 'error')
    return redirect(url_for('festiv_store.master_stock'))

@festiv_store_bp.route('/holi/add-product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'GET':
        return render_template('add_product.html')

    try:
        # 1. Receive and Cleanse Form Data
        base_price = safe_float(request.form.get('base_price'))
        tax_percent = safe_float(request.form.get('tax_percent'))
        profit_margin = safe_float(request.form.get('profit_margin'))
        stock_qty = safe_float(request.form.get('stock'))

        # 2. Secure Backend Calculations
        cost_price = safe_float(request.form.get('cost_price'))
        sell_price = safe_float(request.form.get('sell_price'))
        tax_amount = (base_price * tax_percent) / 100

        # If sell_price was not explicitly sent or is 0, default to base + tax
        if not sell_price:
            sell_price = base_price + tax_amount

        # Calculate profit as per new formula: Sell Price - Cost Price
        profit_margin = sell_price - cost_price

        # 3. Construct Product Payload
        new_product = {
            "store_name": request.form.get('store_name'),
            "product_name": request.form.get('product_name'),
            "brand": request.form.get('brand'),
            "category": request.form.get('category'),
            "price_quantity": request.form.get('price_quantity'),
            "product_unit": request.form.get('product_unit'),
            "cost_price": safe_float(request.form.get('cost_price')),
            "base_price": base_price,
            "tax_percent": tax_percent,
            "tax_amount": tax_amount,
            "profit_margin": profit_margin,
            "sell_price": sell_price,
            "stock": stock_qty,
            "sold_stock": safe_float(request.form.get('sold_stock', 0)),
            "stock_status": request.form.get('stock_status'),
            "product_status": request.form.get('product_status'),
            "last_updated_quantity": stock_qty,
            "created_at": datetime.now().isoformat()
        }

        # 4. Database Insertion
        # Supabase Python client handles parameterization internally
        supabase.table('products').insert(new_product).execute()

        flash('Product added successfully!', 'success')
        return redirect(url_for('festiv_store.master_stock'))

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@festiv_store_bp.route('/holi/ledger')
def ledger():
    period = request.args.get('period', 'all')
    try:
        from datetime import timedelta
        now = datetime.now()
        
        query = supabase.table('bills').select('*').order('created_at', desc=True)
        
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
        elif period == 'week':
            start_date = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
        elif period == 'year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
            
        bills_response = query.execute()
        bills = bills_response.data or []
        
        # To calculate profit per bill, we need bill_items and product margins
        all_items_res = supabase.table('bill_items').select('bill_id, product_id, quantity').execute()
        all_items = all_items_res.data or []
        
        # Fetch product margins
        prods_res = supabase.table('products').select('product_id, profit_margin').execute()
        product_profits = {p['product_id']: safe_float(p.get('profit_margin')) for p in prods_res.data} if prods_res.data else {}
        
        # Group items by bill_id
        items_by_bill = defaultdict(list)
        for item in all_items:
            items_by_bill[item['bill_id']].append(item)
            
        # Attach profit to each bill
        total_revenue = 0
        total_profit = 0
        for b in bills:
            b_id = b.get('bill_id')
            b_profit = 0
            for item in items_by_bill.get(b_id, []):
                p_id = item.get('product_id')
                qty = safe_float(item.get('quantity'))
                margin = product_profits.get(p_id, 0)
                b_profit += (qty * margin)
            
            b['bill_profit'] = b_profit
            total_revenue += safe_float(b.get('bill_total'))
            total_profit += b_profit
            
        total_bills = len(bills)
        
        # --- GRAPH DATA AGGREGATION ---
        graph_labels = []
        graph_data = []
        
        # Sort bills ascending for the graph trend
        sorted_bills = sorted(bills, key=lambda x: x.get('created_at'))
        
        # Helper to format dates for grouping
        def get_group_key(created_at, period):
            # 2024-03-21T14:30:00...
            dt = datetime.fromisoformat(created_at[:19])
            if period == 'day': return dt.strftime('%H:00')
            if period == 'week': return dt.strftime('%a')
            if period == 'month': return dt.strftime('%d %b')
            if period == 'year': return dt.strftime('%B')
            return dt.strftime('%Y-%m-%d')

        trend_map = defaultdict(float)
        for b in sorted_bills:
            key = get_group_key(b.get('created_at'), period)
            trend_map[key] += safe_float(b.get('bill_total'))
        
        if period == 'all':
            # For all time, show last 10 days or months? Let's just use the unique keys sorted
            graph_labels = sorted(trend_map.keys())
        elif period == 'day':
            graph_labels = [f"{h:02d}:00" for h in range(24)]
        elif period == 'week':
            graph_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        elif period == 'month':
            # Approximation of days in current month
            from calendar import monthrange
            days_in_month = monthrange(now.year, now.month)[1]
            graph_labels = [f"{d:02d} {now.strftime('%b')}" for d in range(1, days_in_month + 1)]
        elif period == 'year':
            graph_labels = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        else:
            graph_labels = sorted(trend_map.keys())

        graph_data = [trend_map.get(label, 0) for label in graph_labels]
        
    except Exception as e:
        print(f"Error fetching ledger: {e}")
        bills = []
        total_revenue = 0
        total_bills = 0
        total_profit = 0
        graph_labels = []
        graph_data = []
        
    return render_template('ledger.html', 
                         bills=bills, 
                         total_revenue=total_revenue, 
                         total_bills=total_bills,
                         total_profit=total_profit,
                         active_period=period,
                         graph_labels=graph_labels,
                         graph_data=graph_data)

@festiv_store_bp.route('/holi/make-bill', methods=['GET', 'POST'])
def make_bill():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Invalid JSON data'})
                
            action = data.get('action', 'finalize') # 'prepare' or 'finalize'
            items = data.get('items', [])
            print(f"DEBUG: Processing {len(items)} items for action: {action}")
            
            if not items:
                return jsonify({'success': False, 'message': 'No items in cart'})

            # 1. Validate Stock & Calculate Totals
            total_quantity = 0
            subtotal_amount = 0
            total_tax_amount = 0
            bill_total = 0
            
            validated_items = []
            for item in items:
                try:
                    p_id = item.get('product_id')
                    p_qty = safe_float(item.get('quantity'))
                    
                    if not p_id or p_qty <= 0:
                        continue
                        
                    # SECURITY: Max quantity limit
                    if p_qty > 100:
                        return jsonify({'success': False, 'message': f"Quantity limit exceeded for {item.get('name', 'item')}"})
                    
                    # Fetch fresh product data
                    res = supabase.table('products').select('*').eq('product_id', p_id).execute()
                    if not res.data:
                        return jsonify({'success': False, 'message': f"Product not found: {item.get('name', p_id)}"})
                    
                    prod = res.data[0]
                    p_name = prod.get('product_name', 'Unknown Item')
                    p_stock = safe_float(prod.get('stock', 0))
                    p_sell_price = safe_float(prod.get('sell_price', 0))
                    p_tax_pct = safe_float(prod.get('tax_percent', 0))
                    p_sold_stock = safe_float(prod.get('sold_stock', 0))
                    
                    if p_stock < p_qty:
                         return jsonify({'success': False, 'message': f"Insufficient stock for {p_name} (Available: {p_stock})"})
                    
                    line_total = p_sell_price * p_qty
                    base_price = line_total / (1 + (p_tax_pct/100))
                    tax_amount = line_total - base_price
                    
                    bill_total += line_total
                    subtotal_amount += base_price
                    total_tax_amount += tax_amount
                    total_quantity += p_qty
                    
                    validated_items.append({
                        "product_id": p_id,
                        "name": p_name,
                        "quantity": p_qty,
                        "product_unit": item.get('product_unit', prod.get('product_unit', '-')),
                        "base_price": base_price,
                        "tax_amount": tax_amount,
                        "tax_percent": p_tax_pct,
                        "final_price": p_sell_price,
                        "line_total": line_total,
                        "stock_after": p_stock - p_qty,
                        "sold_stock_after": p_sold_stock + p_qty
                    })
                except Exception as item_err:
                    print(f"DEBUG: Item processing error: {item_err}")
                    continue

            if not validated_items:
                return jsonify({'success': False, 'message': 'No valid items processed'})

            # --- PREPARE PHASE ---
            if action == 'prepare':
                # Generate UPI URL if method is UPI
                upi_url = ""
                payment_method = data.get('payment_method', 'Cash')
                if payment_method == 'UPI':
                    # Generate a unique secure payment reference for tracking
                    payment_ref = PaymentService.generate_secure_reference()
                    upi_url = PaymentService.generate_upi_url(bill_total, payment_ref)
                    
                    # Create a PENDING payment record with backend-calculated amount
                    pending_data = {
                        "payment_reference": payment_ref,
                        "paid_amount": round(bill_total, 2),
                        "payment_method": "UPI",
                        "payment_status": "Pending",
                        "notes": f"Payment for {len(validated_items)} items"
                    }
                    PaymentService.create_pending_payment(supabase, pending_data)
                    
                    return jsonify({
                        'success': True,
                        'action': 'prepared',
                        'bill_total': round(bill_total, 2),
                        'upi_url': upi_url,
                        'payment_ref': payment_ref
                    })
                
                return jsonify({
                    'success': True,
                    'action': 'prepared',
                    'bill_total': round(bill_total, 2),
                    'upi_url': ""
                })

            # 2. Handle Payment Verification (Special logic for UPI)
            payment_ref = data.get('payment_ref')
            payment_method = data.get('payment_method', 'Cash')
            
            if payment_method == 'UPI':
                if not payment_ref:
                    return jsonify({'success': False, 'message': 'Payment reference missing for UPI'})
                
                # Fetch payment record to verify state and amount
                pay_res = supabase.table('payments').select('*').eq('payment_reference', payment_ref).execute()
                if not pay_res.data:
                    return jsonify({'success': False, 'message': 'Payment record not found'})
                
                pay_rec = pay_res.data[0]
                
                # SECURITY: Verify status and amount
                if pay_rec.get('payment_status') != 'Paid':
                    return jsonify({'success': False, 'message': f"Payment status is {pay_rec.get('payment_status')}, not Paid"})
                
                # SECURITY: Verify amount tampering (DB amount vs Calculated amount)
                db_amount = safe_float(pay_rec.get('paid_amount'))
                if abs(db_amount - bill_total) > 0.01:
                    return jsonify({'success': False, 'message': 'Payment amount mismatch detected. Security alert triggered.'})
                
                # PREVENT DUPLICATE: Check if bill already generated (IDEMPOTENCY)
                if pay_rec.get('is_bill_generated'):
                    return jsonify({'success': False, 'message': 'Bill already generated for this payment'})
                
                # Double check bill table for the same payment_id (payment_ref)
                existing_bill = supabase.table('bills').select('bill_id').eq('payment_id', payment_ref).execute()
                if existing_bill.data:
                    return jsonify({'success': False, 'message': 'Bill already exists for this payment reference'})
                
                # SECURITY: Use amount from DB, not frontend
                bill_total = db_amount
            
            # 3. Generate Bill ID/No
            try:
                # Use a cleaner format: HOLI-YYYYMMDD-XXXX
                today_str = datetime.now().strftime("%Y%m%d")
                resp = supabase.table('bills').select('bill_id').order('bill_id', desc=True).limit(1).execute()
                last_id = resp.data[0].get('bill_id', 0) if resp.data else 0
                new_id = last_id + 1
            except:
                new_id = 1
                
            bill_no = f"HOLI-{today_str}-{new_id:04d}"
            
            # 4. Create Bill Record (Aligned with existing schema)
            new_bill = {
                "bill_no": bill_no,
                "store_name": "Holi Store",
                "total_product": len(validated_items),
                "total_quantity": total_quantity,
                "subtotal_amount": round(subtotal_amount, 2),
                "total_tax_amount": round(total_tax_amount, 2),
                "bill_total": round(bill_total, 2),
                "payment_status": "Paid",
                "bill_status": "Completed",
                "payment_id": payment_ref if payment_method == 'UPI' else None,
                "customer_name": data.get('customer_name', 'Cash'),
                "customer_phone": data.get('customer_phone', '-')
            }
            
            print(f"DEBUG: Inserting bill {bill_no}")
            bill_resp = supabase.table('bills').insert(new_bill).execute()
            if not bill_resp.data:
                raise Exception("Failed to insert bill record")
            
            bill_pk = bill_resp.data[0].get('bill_id')
            
            # --- UPDATE PAYMENTS TABLE (Avoid NULLs) ---
            if payment_method == 'UPI' and payment_ref:
                # Link Bill ID to existing UPI payment and mark as handled
                update_pay = {
                    "bill_id": bill_pk,
                    "is_bill_generated": True,
                    "updated_at": datetime.now().isoformat()
                }
                supabase.table('payments').update(update_pay).eq('payment_reference', payment_ref).execute()
            else:
                # Create a Paid payment record for Cash/Other
                cash_payment = {
                    "bill_id": bill_pk,
                    "store_name": "Holi Store",
                    "payment_method": payment_method,
                    "payment_type": "Full",
                    "paid_amount": round(bill_total, 2),
                    "remaining_amount": 0,
                    "payment_status": "Paid",
                    "received_by": "Counter",
                    "payment_reference": f"CASH-{uuid.uuid4().hex[:6].upper()}",
                    "transaction_id": "CASH-TRANSACTION",
                    "is_bill_generated": True,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                supabase.table('payments').insert(cash_payment).execute()
            
            # 4. Insert Items & Update Stock (ATOMIC)
            for v_item in validated_items:
                # Insert Bill Item
                item_data = {
                    "bill_id": bill_pk,
                    "product_id": v_item['product_id'],
                    "product_name": v_item['name'],
                    "quantity": v_item['quantity'],
                    "product_unit": v_item['product_unit'],
                    "base_price": v_item['base_price'],
                    "tax_percent": v_item['tax_percent'],
                    "tax_amount": v_item['tax_amount'],
                    "final_price": v_item['final_price'],
                    "total_price": v_item['line_total']
                }
                supabase.table('bill_items').insert(item_data).execute()
                
                # Update stock and sold_stock based on verified quantities
                update_res = supabase.table('products').update({
                    'stock': v_item['stock_after'],
                    'sold_stock': v_item['sold_stock_after']
                }).eq('product_id', v_item['product_id']).execute()
                
                if not update_res.data:
                    print(f"CRITICAL: Stock update failed during finalization for {v_item['name']}")
                    # Note: Ideally we should rollback the bill here if stock fails, 
                    # but Supabase Python client doesn't support transactions easily outside RPC.
                    # This check at least detects it.

            # 5. PDF Generation & Local Storage
            bill_url = None
            try:
                # Pass data for PDF display
                pdf_data = new_bill.copy()
                pdf_data['customer_name'] = data.get('customer_name', 'Cash')
                pdf_data['customer_phone'] = data.get('customer_phone', '-')
                pdf_data['payment_method'] = data.get('payment_method', 'Cash')
                pdf_data['bill_date'] = datetime.now().strftime("%Y-%m-%d")
                pdf_data['bill_time'] = datetime.now().strftime("%H:%M:%S")
                
                pdf_buf = generate_bill_pdf(pdf_data, validated_items)
                
                # Local Storage Path
                # Get the absolute path to the static/bills directory
                # Since this file is in static/python/, we go up one level
                static_bills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bills'))
                if not os.path.exists(static_bills_dir):
                    os.makedirs(static_bills_dir)
                
                local_file_path = os.path.join(static_bills_dir, f"{bill_no}.pdf")
                with open(local_file_path, 'wb') as f:
                    f.write(pdf_buf.getvalue())
                
                # Use url_for to generate the static URL correctly
                bill_url = url_for('festiv_store.static', filename=f'bills/{bill_no}.pdf')
                
                # Optional: Still upload to Supabase if config is available
                try:
                    supabase_path = f"bills/{bill_no}.pdf"
                    supabase.storage.from_('bills').upload(
                        path=supabase_path,
                        file=pdf_buf.getvalue(),
                        file_options={"content-type": "application/pdf"}
                    )
                    # Uncomment if you want the public URL from Supabase to be the one in DB
                    # bill_url = supabase.storage.from_('bills').get_public_url(supabase_path)
                except Exception as s_err:
                    print(f"DEBUG: Supabase Storage Error (continuing with local): {s_err}")
                
                # Save URL to database
                try:
                    # Update Bills table
                    supabase.table('bills').update({"bill_url": bill_url}).eq('bill_id', bill_pk).execute()
                    
                    # Update Payments table as well
                    if payment_method == 'UPI' and payment_ref:
                        supabase.table('payments').update({"bill_url": bill_url}).eq('payment_reference', payment_ref).execute()
                    else:
                        # For Cash, update by bill_id
                        supabase.table('payments').update({"bill_url": bill_url}).eq('bill_id', bill_pk).execute()
                        
                except Exception as db_err:
                    print(f"DEBUG: Database update failed: {db_err}")
            except Exception as pdf_err:
                print(f"DEBUG: PDF Error: {pdf_err}")

            return jsonify({'success': True, 'bill_no': bill_no, 'bill_url': bill_url})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': f"Internal Error: {str(e)}"})

    # GET Request
    try:
        # Filter: Only show products with 'Active' status on the billing page
        products_response = supabase.table('products').select('*').eq('product_status', 'Active').execute()
        products = products_response.data or []
    except:
        products = []
            
    return render_template('make_bill.html', products=products)

@festiv_store_bp.route('/holi/api/check-payment-status/<payment_ref>')
def check_payment_status(payment_ref):
    status = PaymentService.check_status(supabase, payment_ref)
    # Return exact JSON format as requested: {"status": "Pending" | "Paid" | "Expired"}
    return jsonify({'status': status})

@festiv_store_bp.route('/holi/api/verify-upi-payment/<payment_ref>', methods=['POST'])
def verify_upi_payment(payment_ref):
    """
    Manually marks a payment as Paid. Used as fallback when auto-detection is slow.
    """
    try:
        success = PaymentService.mark_as_paid(supabase, payment_ref, f"MAN-{uuid.uuid4().hex[:10].upper()}")
        return jsonify({'success': success, 'message': 'Payment confirmed successfully' if success else 'Reference not found'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f"Server error: {str(e)}"})

@festiv_store_bp.route('/holi/payment-data')
def payment_data():
    period = request.args.get('period', 'all')
    try:
        from datetime import timedelta
        now = datetime.now()
        
        query = supabase.table('payments').select('*, bills(bill_no)').order('created_at', desc=True)
        
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
        elif period == 'week':
            start_date = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
        elif period == 'year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte('created_at', start_date)
            
        payments_response = query.execute()
        payments = payments_response.data or []
        
        # Calculate summaries
        cash_payments = [p for p in payments if p.get('payment_method') == 'Cash']
        upi_payments = [p for p in payments if p.get('payment_method') == 'UPI']
        
        cash_total = sum(safe_float(p.get('paid_amount')) for p in cash_payments)
        upi_total = sum(safe_float(p.get('paid_amount')) for p in upi_payments)
        
        cash_count = len(cash_payments)
        upi_count = len(upi_payments)
        
    except Exception as e:
        print(f"Error fetching payment data: {e}")
        payments = []
        cash_total = 0
        upi_total = 0
        cash_count = 0
        upi_count = 0
        
    return render_template('payment_data.html', 
                         payments=payments, 
                         cash_total=cash_total, 
                         upi_total=upi_total,
                         cash_count=cash_count,
                         upi_count=upi_count,
                         active_period=period)
