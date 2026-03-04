from datetime import datetime
import uuid
import os
import io
from flask import render_template, request, jsonify, url_for
from .. import main_store_bp
from database.db import supabase
from ..utils.payment_service import PaymentService
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

def generate_bill_pdf(bill_data, items):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, alignment=1, spaceAfter=2, textColor=colors.black)
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontSize=12, alignment=1, spaceAfter=10)
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=9)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')

    elements.append(Paragraph("<b>BIG TULSHI SHOP</b>", title_style))
    elements.append(Paragraph("MAIN STORE", subtitle_style))
    
    elements.append(Paragraph("<b>TAX INVOICE</b>", ParagraphStyle('TaxStyle', parent=styles['Normal'], fontSize=12, alignment=1)))
    elements.append(Paragraph("Original", ParagraphStyle('OriginalStyle', parent=styles['Normal'], fontSize=8, alignment=1, spaceAfter=10)))
    
    elements.append(Spacer(1, 0.1 * inch))

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

    table_data = [['Sr', 'Description', 'HSN', 'Qty', 'Rate', 'Taxable', 'CGST', 'SGST', 'Amount']]
    
    for i, item in enumerate(items, 1):
        tax_amt = safe_float(item.get('tax_amount', 0))
        cgst_sgst_amt = tax_amt / 2
        tax_pct = safe_float(item.get('tax_percent', 0))
        cgst_sgst_pct = tax_pct / 2
        
        row = [
            str(i),
            Paragraph(f"{item['name']}", info_style),
            "0910", # Placeholder
            str(item['quantity']),
            f"{item['final_price']:.2f}",
            f"{item['base_price']:.2f}",
            f"{cgst_sgst_pct:.2f}%",
            f"{cgst_sgst_pct:.2f}%",
            f"{item['line_total']:.2f}"
        ]
        table_data.append(row)

    items_table = Table(table_data, colWidths=[0.3*inch, 2.2*inch, 0.6*inch, 0.5*inch, 0.7*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.8*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.2 * inch))

    totals_data = [
        ['', '', '', '', '', 'Taxable Amt', f"{bill_data['subtotal_amount']:.2f}"],
        ['', '', '', '', '', 'CGST Amt', f"{(bill_data['total_tax_amount']/2):.2f}"],
        ['', '', '', '', '', 'SGST Amt', f"{(bill_data['total_tax_amount']/2):.2f}"],
        ['', '', '', '', '', Paragraph('<b>Grand Total</b>', header_style), Paragraph(f"<b>Rs.{bill_data['bill_total']:.2f}</b>", header_style)]
    ]
    
    totals_table = Table(totals_data, colWidths=[0.3*inch, 2.2*inch, 0.6*inch, 0.5*inch, 0.7*inch, 1.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (-2, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (-2, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(totals_table)
    
    elements.append(Spacer(1, 0.5 * inch))
    
    elements.append(Paragraph("Certified that particulars given above are true and correct.", info_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    elements.append(Paragraph(f"For, <b>BIG TULSHI SHOP</b>", ParagraphStyle('FooterStyle', parent=styles['Normal'], fontSize=10, alignment=2)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

@main_store_bp.route('/make-bill', methods=['GET', 'POST'])
def make_bill():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Invalid JSON data'})
                
            action = data.get('action', 'finalize')
            items = data.get('items', [])
            
            if not items:
                return jsonify({'success': False, 'message': 'No items in cart'})

            total_quantity = 0
            subtotal_amount = 0
            total_tax_amount = 0
            bill_total = 0
            validated_items = []
            
            for item in items:
                try:
                    p_id = item.get('product_id')
                    p_qty = safe_float(item.get('quantity'))
                    
                    if not p_id or p_qty <= 0: continue
                    if p_qty > 100:
                        return jsonify({'success': False, 'message': f"Quantity limit exceeded for {item.get('name', 'item')}"})
                    
                    res = supabase.table('products').select('*').eq('product_id', p_id).execute()
                    if not res.data:
                        return jsonify({'success': False, 'message': f"Product not found: {item.get('name', p_id)}"})
                    
                    prod = res.data[0]
                    p_name = prod.get('product_name', 'Unknown Item')
                    p_stock = safe_float(prod.get('stock', 0))
                    p_sell_price = safe_float(prod.get('sell_price', 0))
                    p_tax_pct = safe_float(prod.get('tax_percent', 0))
                    p_sold_stock = safe_float(prod.get('sold_stock', 0))
                    p_cost_price = safe_float(prod.get('cost_price', 0))
                    p_profit_margin = safe_float(prod.get('profit_margin', 0))
                    
                    if p_stock < p_qty:
                         return jsonify({'success': False, 'message': f"Insufficient stock for {p_name} (Available: {p_stock})"})
                    
                    # Accept custom final price from frontend for Credit bills, otherwise use DB price
                    payment_method = data.get('payment_method', 'Cash')
                    if payment_method in ['Credit', 'Wholesale']:
                        custom_price = item.get('final_price')
                        if custom_price is not None:
                            p_sell_price = safe_float(custom_price)
                            # Custom profit margin for credit/wholesale bills
                            p_profit_margin = p_sell_price - p_cost_price

                    
                    line_total = round(p_sell_price * p_qty)
                    base_price = line_total / (1 + (p_tax_pct/100))
                    tax_amount = round(line_total - base_price)
                    
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
                        "profit_margin": p_profit_margin,
                        "line_total": line_total,
                        "stock_after": p_stock - p_qty,
                        "sold_stock_after": p_sold_stock + p_qty
                    })
                except Exception as item_err:
                    continue

            if not validated_items:
                return jsonify({'success': False, 'message': 'No valid items processed'})

            if action == 'prepare':
                payment_method = data.get('payment_method', 'Cash')
                if payment_method == 'UPI':
                    payment_ref = PaymentService.generate_secure_reference()
                    upi_url = PaymentService.generate_upi_url(bill_total, payment_ref)
                    
                    pending_data = {
                        "payment_reference": payment_ref,
                        "paid_amount": round(bill_total, 2),
                        "payment_method": "UPI",
                        "payment_status": "Pending",
                        "notes": f"Payment for {len(validated_items)} items",
                        "store_name": "Main Store"
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

            payment_ref = data.get('payment_ref')
            payment_method = data.get('payment_method', 'Cash')
            
            if payment_method == 'UPI':
                if not payment_ref:
                    return jsonify({'success': False, 'message': 'Payment reference missing for UPI'})
                
                pay_res = supabase.table('payments').select('*').eq('payment_reference', payment_ref).execute()
                if not pay_res.data:
                    return jsonify({'success': False, 'message': 'Payment record not found'})
                
                pay_rec = pay_res.data[0]
                
                if pay_rec.get('payment_status') != 'Paid':
                    return jsonify({'success': False, 'message': f"Payment status is {pay_rec.get('payment_status')}, not Paid"})
                
                db_amount = safe_float(pay_rec.get('paid_amount'))
                if abs(db_amount - bill_total) > 0.01:
                    return jsonify({'success': False, 'message': 'Payment amount mismatch detected.'})
                
                if pay_rec.get('is_bill_generated'):
                    return jsonify({'success': False, 'message': 'Bill already generated for this payment'})
                
                existing_bill = supabase.table('bills').select('bill_id').eq('payment_id', payment_ref).execute()
                if existing_bill.data:
                    return jsonify({'success': False, 'message': 'Bill already exists for this payment reference'})
                
                bill_total = db_amount
            
            try:
                today_str = datetime.now().strftime("%Y%m%d")
                resp = supabase.table('bills').select('bill_id').order('bill_id', desc=True).limit(1).execute()
                last_id = resp.data[0].get('bill_id', 0) if resp.data else 0
                new_id = last_id + 1
            except:
                new_id = 1
                
            bill_no = f"MAIN-{today_str}-{new_id:04d}"
            
            new_bill = {
                "bill_no": bill_no,
                "store_name": "Main Store",
                "total_product": len(validated_items),
                "total_quantity": total_quantity,
                "subtotal_amount": round(subtotal_amount, 2),
                "total_tax_amount": round(total_tax_amount, 2),
                "bill_total": round(bill_total, 2),
                "payment_status": "Paid" if payment_method != 'Credit' else "Pending",
                "bill_status": "Completed" if payment_method != 'Credit' else "Pending",
                "payment_id": payment_ref if payment_method == 'UPI' else None,
                "payment_method": payment_method,
                "customer_name": data.get('customer_name', 'Cash'),
                "customer_phone": data.get('customer_phone') or 'N/A'
            }
            
            bill_resp = supabase.table('bills').insert(new_bill).execute()
            if not bill_resp.data:
                raise Exception("Failed to insert bill record")
            
            bill_pk = bill_resp.data[0].get('bill_id')
            
            if payment_method == 'UPI' and payment_ref:
                update_pay = {
                    "bill_id": bill_pk,
                    "is_bill_generated": True,
                    "updated_at": datetime.now().isoformat()
                }
                supabase.table('payments').update(update_pay).eq('payment_reference', payment_ref).execute()
            else:
                cash_payment = {
                    "bill_id": bill_pk,
                    "store_name": "Main Store",
                    "payment_method": payment_method,
                    "payment_type": "Full" if payment_method != 'Credit' else "Partial",
                    "paid_amount": round(bill_total, 2) if payment_method != 'Credit' else 0,
                    "remaining_amount": 0 if payment_method != 'Credit' else round(bill_total, 2),
                    "payment_status": "Paid" if payment_method != 'Credit' else "Pending",
                    "received_by": "Counter",
                    "payment_reference": f"{payment_method.upper()}-{uuid.uuid4().hex[:10].upper()}",
                    "transaction_id": f"{payment_method.upper()}-AUTO-{uuid.uuid4().hex[:6].upper()}",
                    "is_bill_generated": True,
                    "notes": f"Initial record for {payment_method} bill",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                supabase.table('payments').insert(cash_payment).execute()
            
            for v_item in validated_items:
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
                    "profit_margin": v_item['profit_margin'],
                    "total_price": v_item['line_total']
                }
                supabase.table('bill_items').insert(item_data).execute()
                
                supabase.table('products').update({
                    'stock': v_item['stock_after'],
                    'sold_stock': v_item['sold_stock_after']
                }).eq('product_id', v_item['product_id']).execute()

            bill_url = None
            try:
                pdf_data = new_bill.copy()
                pdf_data['customer_name'] = data.get('customer_name', 'Cash')
                pdf_data['customer_phone'] = data.get('customer_phone') or 'N/A'
                pdf_data['payment_method'] = data.get('payment_method', 'Cash')
                pdf_data['bill_date'] = datetime.now().strftime("%Y-%m-%d")
                pdf_data['bill_time'] = datetime.now().strftime("%H:%M:%S")
                
                pdf_buf = generate_bill_pdf(pdf_data, validated_items)
                
                static_bills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'bills'))
                if not os.path.exists(static_bills_dir):
                    os.makedirs(static_bills_dir)
                
                local_file_path = os.path.join(static_bills_dir, f"{bill_no}.pdf")
                with open(local_file_path, 'wb') as f:
                    f.write(pdf_buf.getvalue())
                
                bill_url = url_for('main_store.static', filename=f'bills/{bill_no}.pdf')
                
                try:
                    supabase.table('bills').update({"bill_url": bill_url}).eq('bill_id', bill_pk).execute()
                    
                    if payment_method == 'UPI' and payment_ref:
                        supabase.table('payments').update({"bill_url": bill_url}).eq('payment_reference', payment_ref).execute()
                    else:
                        supabase.table('payments').update({"bill_url": bill_url}).eq('bill_id', bill_pk).execute()
                except:
                    pass
            except:
                pass
                
            if payment_method == 'Credit':
                customer_phone = data.get('customer_phone') or 'N/A'
                customer_name = data.get('customer_name', 'Cash')
                
                cust_res = supabase.table('customer').select('*').eq('phone_no', customer_phone).execute()
                cust = None
                if cust_res.data:
                    cust = cust_res.data[0]
                else:
                    new_cust = {
                        "name": customer_name,
                        "phone_no": customer_phone,
                        "address": "-",
                        "padin_amount_last": 0,
                        "padin_amount_total": 0,
                        "panding_bill_count": 0,
                        "all_bill_count": 0,
                        "status": "Active",
                        "created_by": "System"
                    }
                    try:
                        ins_cust = supabase.table('customer').insert(new_cust).execute()
                        if ins_cust.data:
                            cust = ins_cust.data[0]
                    except:
                        pass
                
                if cust:
                    updated_padin_total = float(cust.get('padin_amount_total', 0) or 0) + round(bill_total, 2)
                    try:
                        supabase.table('customer').update({
                            "padin_amount_last": round(bill_total, 2),
                            "padin_amount_total": round(updated_padin_total, 2),
                            "panding_bill_count": int(cust.get('panding_bill_count', 0) or 0) + 1,
                            "all_bill_count": int(cust.get('all_bill_count', 0) or 0) + 1,
                            "last_payment_date": datetime.now().isoformat()
                        }).eq('id', cust['id']).execute()
                        
                        bill_desc = ", ".join([f"{item['name']} ({item['quantity']}{item['product_unit']} x {item['final_price']})" for item in validated_items])
                        credit_bill_data = {
                            "c_id": cust['id'],
                            "bill_id": bill_pk,
                            "bill_url": bill_url or "-",
                            "total_price": round(bill_total, 2),
                            "paid_amount": 0,
                            "remaining_amount": round(bill_total, 2),
                            "bill_discreption": bill_desc,
                            "bill_status": "Pending",
                            "payment_status": "Unpaid",
                            "payment_method": "Credit",
                            "payment_date": datetime.now().isoformat(),
                            "created_date": datetime.now().strftime("%Y-%m-%d"),
                            "created_time": datetime.now().strftime("%H:%M:%S"),
                            "created_by": "System",
                            "created_at": datetime.now().isoformat()
                        }
                        supabase.table('credit_bill').insert(credit_bill_data).execute()
                    except Exception as ex:
                        print("Error saving credit bill:", ex)

            return jsonify({'success': True, 'bill_no': bill_no, 'bill_url': bill_url})

        except Exception as e:
            return jsonify({'success': False, 'message': f"Internal Error: {str(e)}"})

    try:
        products_response = supabase.table('products').select('*').eq('store_name', 'Main Store').eq('product_status', 'Active').execute()
        products = products_response.data or []
    except:
        products = []
        
    try:
        customers_response = supabase.table('customer').select('*').eq('status', 'Active').execute()
        customers = customers_response.data or []
    except:
        customers = []
            
    return render_template('make_bill_main.html', products=products, customers=customers)
