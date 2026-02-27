import os
import re

template_dir = r"d:\shop\main_store\templates"
base_file = r"d:\shop\templates\base.html"

# Ensure meta viewport is in base.html
with open(base_file, 'r', encoding='utf-8') as f:
    base_content = f.read()

if '<meta name="viewport"' not in base_content:
    print("Adding viewport meta tag to base.html")
    base_content = base_content.replace('<head>', '<head>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">')
    with open(base_file, 'w', encoding='utf-8') as f:
        f.write(base_content)

# Add generic table scroll wrapper & mobile padding to all templates if missing
wrap_start = '<div class="table-responsive" style="overflow-x: auto; -webkit-overflow-scrolling: touch;">\n\\1'
wrap_end = '\\1\n</div>'

for filename in os.listdir(template_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(template_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        modified = False
        
        # 1. Wrap raw tables not already in a wrapper
        if '<table' in content and 'table-responsive' not in content and 'elite-table-wrapper' not in content:
            content = re.sub(r'(<table[^>]*>.*?</table\s*>)', wrap_start, content, flags=re.DOTALL)
            content = content.replace("</table>", "</table>\n</div>")
            modified = True
            
        # 2. Add padding to main container for mobile if it's missing
        if 'padding' not in content and 'container' in content:
            # Inject a quick style block just before {% endblock %} or at the end
            mobile_style = """
<style>
    @media (max-width: 768px) {
        .container, .main-container, .dashboard-container {
            padding: 10px !important;
        }
        .card { margin-bottom: 15px !important; }
    }
</style>
"""
            if '{% endblock' in content:
                content = content.replace('{% block extra_css %}\n{{ super() }}', '{% block extra_css %}\n{{ super() }}' + mobile_style)
                modified = True
                
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated responsive styles in {filename}")

print("Responsive CSS pass complete.")
