import os

src_path = r"d:\shop\festiv_store\holi\templates\payment_data.html"
dst_path = r"d:\shop\main_store\templates\payments_main.html"

with open(src_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make route and branding adjustments
content = content.replace("url_for('festiv_store.", "url_for('main_store.")
content = content.replace("Holi Store", "Main Store")
content = content.replace("HOLI STORE", "MAIN STORE")
content = content.replace("{% extends 'holi_base.html' %}", "{% extends 'base.html' %}")

# Make sure the period filter links point to main_store.payments instead of main_store.payment_data if not already updated
content = content.replace("url_for('main_store.payment_data'", "url_for('main_store.payments'")

with open(dst_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Successfully copied and updated payment data template.")
