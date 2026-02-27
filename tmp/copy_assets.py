import os
import shutil

src_css = r"d:\shop\festiv_store\holi\static\css"
src_js = r"d:\shop\festiv_store\holi\static\js"
dst_css = r"d:\shop\main_store\static\css"
dst_js = r"d:\shop\main_store\static\js"

os.makedirs(dst_css, exist_ok=True)
os.makedirs(dst_js, exist_ok=True)

# Copy CSS
for file in os.listdir(src_css):
    if file.endswith('.css'):
        src_path = os.path.join(src_css, file)
        dst_path = os.path.join(dst_css, file)
        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Optional renaming/theming
        content = content.replace("Holi Store", "Main Store")
        content = content.replace("HOLI STORE", "MAIN STORE")
        
        with open(dst_path, 'w', encoding='utf-8') as f:
            f.write(content)

# Copy JS
for file in os.listdir(src_js):
    if file.endswith('.js'):
        src_path = os.path.join(src_js, file)
        dst_path = os.path.join(dst_js, file)
        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        content = content.replace("url_for('festiv_store.", "url_for('main_store.")
        content = content.replace("/festiv_store/", "/main_store/")
        
        with open(dst_path, 'w', encoding='utf-8') as f:
            f.write(content)

print("CSS and JS files copied successfully to main_store/static.")
