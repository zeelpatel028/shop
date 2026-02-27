import os

src_dir = r"d:\shop\festiv_store\holi\templates"
dst_dir = r"d:\shop\main_store\templates"

files_to_copy = {
    'master_stock.html': 'master_stock_main.html',
    'make_bill.html': 'make_bill_main.html',
    'ledger.html': 'ledger_main.html',
    'add_product.html': 'add_product_main.html'
}

for src_name, dst_name in files_to_copy.items():
    src_path = os.path.join(src_dir, src_name)
    dst_path = os.path.join(dst_dir, dst_name)
    
    with open(src_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace URLs routing
    content = content.replace("url_for('festiv_store.", "url_for('main_store.")
    
    # Replace text branding
    content = content.replace("Holi Store", "Main Store")
    content = content.replace("HOLI STORE", "MAIN STORE")
    
    # Replace base template inheritances
    content = content.replace("{% extends 'holi_base.html' %}", "{% extends 'base.html' %}")
    content = content.replace("{% extends \"holi_base.html\" %}", "{% extends 'base.html' %}")

    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(content)

print(f"Successfully copied and updated {len(files_to_copy)} templates.")
