// State
let cart = [];
let products = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    try {
        const rawData = document.getElementById('productsData').textContent;
        products = JSON.parse(rawData);
        console.log("Loaded products:", products.length);
    } catch (e) {
        console.error("Error loading product data", e);
    }

    renderCart();
});

// --- Core Functions ---

function addToCart(productId) {
    // Find product
    const product = products.find(p => String(p.id) === String(productId));
    if (!product) return;

    // Check if exists in cart
    const existingItem = cart.find(item => String(item.id) === String(productId));

    if (existingItem) {
        if (existingItem.quantity < product.stock) {
            existingItem.quantity++;
        } else {
            showToast("Insufficient stock!", "error");
            return;
        }
    } else {
        if (product.stock <= 0) {
            showToast("Product is out of stock!", "error");
            return;
        }
        // Add new item
        cart.push({
            id: product.id,
            name: product.product_name || product.name,
            price: parseFloat(product.base_price || product.price || 0),
            final_price: parseFloat(product.final_price || product.price || 0),
            tax_percent: parseFloat(product.tax_percent || 0),
            stock: product.stock,
            quantity: 1
        });
    }

    renderCart();
    playBeep();
}

function updateQty(index, change) {
    const item = cart[index];
    const newQty = item.quantity + change;

    if (newQty > 0) {
        if (newQty <= item.stock) {
            item.quantity = newQty;
        } else {
            showToast(`Only ${item.stock} items in stock!`, "warning");
        }
    } else {
        // Confirm removal if qty goes to 0? Or just stay at 1?
        // Usually stay at 1 or remove. Let's remove if explicit remove button is used, 
        // but for minus button, maybe stop at 1.
        item.quantity = 1;
    }
    renderCart();
}

function removeFromCart(index) {
    cart.splice(index, 1);
    renderCart();
}

function clearCart() {
    if (cart.length > 0 && confirm("Are you sure you want to clear the cart?")) {
        cart = [];
        renderCart();
    }
}

// --- Rendering ---

function renderCart() {
    const container = document.getElementById('cartItemsContainer');

    if (cart.length === 0) {
        container.innerHTML = `
            <div class="empty-cart-message">
                <i class="fas fa-basket-shopping" style="font-size: 30px; color: #ddd; margin-bottom: 10px;"></i>
                <p style="color: #999;">Cart is empty</p>
            </div>`;
        updateTotals();
        return;
    }

    let html = '';
    cart.forEach((item, index) => {
        const total = item.final_price * item.quantity;
        html += `
        <div class="cart-item">
            <div class="cart-item-info">
                <div class="cart-item-title">${item.name}</div>
                <div class="cart-item-price">₹${item.final_price.toFixed(2)} x ${item.quantity}</div>
            </div>
            <div class="cart-controls">
                <div class="qty-btn" onclick="updateQty(${index}, -1)">-</div>
                <div class="qty-display">${item.quantity}</div>
                <div class="qty-btn" onclick="updateQty(${index}, 1)">+</div>
                <div class="item-total-price">₹${total.toFixed(2)}</div>
                <i class="fas fa-trash-alt remove-item-btn" onclick="removeFromCart(${index})" title="Remove"></i>
            </div>
        </div>`;
    });

    container.innerHTML = html;

    // Auto scroll to bottom if new item added?
    // container.scrollTop = container.scrollHeight;

    updateTotals();
}

function updateTotals() {
    let subtotal = 0;
    let tax = 0;
    let total = 0;

    cart.forEach(item => {
        const itemTotal = item.final_price * item.quantity;
        total += itemTotal;

        // Back calculate tax
        // Base = Final / (1 + tax_rate/100)
        const taxRate = item.tax_percent || 0;
        const baseTotal = itemTotal / (1 + (taxRate / 100));

        subtotal += baseTotal;
        tax += (itemTotal - baseTotal);
    });

    document.getElementById('subTotal').innerText = '₹' + subtotal.toFixed(2);
    document.getElementById('taxTotal').innerText = '₹' + tax.toFixed(2);
    document.getElementById('grandTotal').innerText = '₹' + total.toFixed(2);

    // Disable checkout if empty
    const btn = document.getElementById('checkoutBtn');
    if (cart.length === 0) {
        btn.style.opacity = '0.5';
        btn.style.pointerEvents = 'none';
    } else {
        btn.style.opacity = '1';
        btn.style.pointerEvents = 'auto';
    }
}

// --- Search ---

document.getElementById('productSearch').addEventListener('input', function (e) {
    const term = e.target.value.toLowerCase();
    const cards = document.querySelectorAll('.product-card');
    let hasResults = false;

    cards.forEach(card => {
        const name = card.getAttribute('data-name').toLowerCase();
        const category = card.getAttribute('data-category').toLowerCase();

        if (name.includes(term) || category.includes(term)) {
            card.style.display = 'flex';
            hasResults = true;
        } else {
            card.style.display = 'none';
        }
    });

    const noResults = document.getElementById('noResultsMsg');
    if (!hasResults && term !== '') {
        noResults.style.display = 'block';
    } else {
        noResults.style.display = 'none';
    }
});

// --- Checkout ---

function processCheckout() {
    if (cart.length === 0) return;

    const customerName = document.getElementById('customerName').value;
    const customerPhone = document.getElementById('customerPhone').value;
    const btn = document.getElementById('checkoutBtn');

    // Loading state
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    btn.disabled = true;

    const payload = {
        customer_name: customerName,
        customer_phone: customerPhone,
        items: cart
    };

    // Use global constant MAKE_BILL_URL
    fetch(MAKE_BILL_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Success animation or redirect
                showToast("Bill Generated Successfully!", "success");
                setTimeout(() => {
                    // Use global constant LEDGER_URL
                    window.location.href = LEDGER_URL;
                }, 1000);
            } else {
                alert('Error: ' + data.message);
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('An error occurred during checkout');
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

// --- Utilities ---

function showToast(msg, type = 'info') {
    // Simple alert for now, can be upgraded to custom toast
    // Creating a temporary toast element
    const toast = document.createElement('div');
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.padding = '12px 24px';
    toast.style.borderRadius = '8px';
    toast.style.color = '#fff';
    toast.style.fontWeight = '500';
    toast.style.zIndex = '1000';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';

    if (type === 'error') toast.style.backgroundColor = '#ff4d4d';
    else if (type === 'success') toast.style.backgroundColor = '#2ecc71';
    else if (type === 'warning') toast.style.backgroundColor = '#ff9f43';
    else toast.style.backgroundColor = '#333';

    toast.innerText = msg;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function playBeep() {
    // Optional: Play a subtle sound when adding to cart
    // const audio = new Audio('/static/sounds/beep.mp3');
    // audio.play().catch(e => console.log('Audio play failed', e));
}
