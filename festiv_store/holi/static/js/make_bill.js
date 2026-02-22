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
    setupPaymentMethodListener();
});

function setupPaymentMethodListener() {
    const paymentSelect = document.getElementById('paymentMethod');
    const checkoutBtnSpan = document.querySelector('#checkoutBtn span');

    if (paymentSelect && checkoutBtnSpan) {
        paymentSelect.addEventListener('change', () => {
            const method = paymentSelect.value;
            if (method === 'UPI') {
                checkoutBtnSpan.innerText = 'Pay and Generate Bill';
            } else {
                checkoutBtnSpan.innerText = 'Generate Bill';
            }
        });
    }
}

// --- Core Functions ---

function addToCart(productId) {
    // Find product
    const product = products.find(p => String(p.product_id) === String(productId));
    if (!product) return;

    if (product.stock <= 0) {
        showToast("Product is out of stock!", "error");
        return;
    }

    // Prepare Modal
    document.getElementById('qtyProductId').value = productId;
    document.getElementById('qtyModalTitle').innerText = `Add ${product.product_name || product.name}`;
    document.getElementById('qtyModalStock').innerText = `${product.stock} ${product.product_unit || 'unit'}`;
    document.getElementById('qtyInput').value = '1';

    const unitSelect = document.getElementById('unitSelect');
    const baseUnit = (product.product_unit || '').toLowerCase();

    // Dynamically populate unit options based on product's base unit
    let options = '';
    if (baseUnit === 'kg' || baseUnit === 'kilogram') {
        options = `<option value="kg">kg</option><option value="g">g</option>`;
    } else if (baseUnit === 'ltr' || baseUnit === 'liter' || baseUnit === 'l') {
        options = `<option value="ltr">ltr</option><option value="ml">ml</option>`;
    } else if (baseUnit === 'g' || baseUnit === 'gram') {
        options = `<option value="g">g</option><option value="kg">kg</option>`;
    } else {
        options = `<option value="${baseUnit || 'pcs'}">${baseUnit || 'pcs'}</option>`;
    }

    unitSelect.innerHTML = options;

    // Show Modal
    document.getElementById('qtyModal').style.display = 'flex';
}

function closeQtyModal() {
    document.getElementById('qtyModal').style.display = 'none';
}

function confirmAddQty() {
    const productId = document.getElementById('qtyProductId').value;
    const qtyInputValue = parseFloat(document.getElementById('qtyInput').value);
    const selectedUnit = document.getElementById('unitSelect').value;

    if (isNaN(qtyInputValue) || qtyInputValue <= 0) {
        showToast("Please enter a valid quantity", "warning");
        return;
    }

    const product = products.find(p => String(p.product_id) === String(productId));
    const baseUnit = (product.product_unit || '').toLowerCase();

    // CONVERT TO BASE UNIT QUANTITY
    let baseQty = qtyInputValue;

    if (baseUnit === 'kg' && selectedUnit === 'g') {
        baseQty = qtyInputValue / 1000;
    } else if (baseUnit === 'g' && selectedUnit === 'kg') {
        baseQty = qtyInputValue * 1000;
    } else if (baseUnit === 'ltr' && selectedUnit === 'ml') {
        baseQty = qtyInputValue / 1000;
    }

    // Check if exists in cart
    let existingItem = cart.find(item => String(item.product_id) === String(productId));
    let totalQtyRequested = existingItem ? existingItem.quantity + baseQty : baseQty;

    if (totalQtyRequested > product.stock) {
        showToast(`Insufficient stock! Only ${product.stock} ${baseUnit} available.`, "error");
        return;
    }

    if (existingItem) {
        existingItem.quantity += baseQty;
        // Optionally store the last display string
        existingItem.displayQty = `${qtyInputValue} ${selectedUnit}`;
    } else {
        // Add new item
        cart.push({
            product_id: product.product_id,
            name: product.product_name || product.name,
            brand: product.brand || '-',
            product_unit: product.product_unit || '-',
            price: parseFloat(product.base_price || 0),
            final_price: parseFloat(product.sell_price || product.final_price || product.price || 0),
            tax_percent: parseFloat(product.tax_percent || 0),
            stock: product.stock,
            quantity: baseQty,
            displayQty: `${qtyInputValue} ${selectedUnit}`
        });
    }

    closeQtyModal();
    renderCart();
    playBeep();
}

function updateQty(index, change) {
    const item = cart[index];
    // Since quantities can be floats (like 0.5), simple +/- 1 might not make sense for fractional things.
    // However, we'll keep it as +/- 1 for ease of use, but ensure it supports floats properly.
    const newQty = item.quantity + change;

    if (newQty > 0) {
        if (newQty <= item.stock) {
            item.quantity = newQty;
            item.displayQty = `${newQty} ${item.product_unit}`; // Reset display to base units if tweaked via +/-
        } else {
            showToast(`Only ${item.stock} items in stock!`, "warning");
        }
    } else {
        item.quantity = 1;
        item.displayQty = `1 ${item.product_unit}`;
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
        // Clean display formatting for floats
        const cleanQty = Number.isInteger(item.quantity) ? item.quantity : item.quantity.toFixed(3).replace(/\.?0+$/, '');

        html += `
        <div class="cart-item">
            <div class="cart-item-info">
                <div class="cart-item-title">${item.name}</div>
                <div class="cart-item-subtext">${item.brand} | ${item.displayQty || (cleanQty + ' ' + item.product_unit)}</div>
                <div class="cart-item-price">₹${item.final_price.toFixed(2)}/unit</div>
            </div>
            <div class="cart-controls">
                <div class="qty-btn" onclick="updateQty(${index}, -1)" title="- 1 Unit">-</div>
                <div class="qty-display" style="width: auto; min-width: 35px; font-size: 12px;" title="Base Quantity">${cleanQty}</div>
                <div class="qty-btn" onclick="updateQty(${index}, 1)" title="+ 1 Unit">+</div>
                <div class="item-total-price">₹${total.toFixed(2)}</div>
                <i class="fas fa-trash-alt remove-item-btn" onclick="removeFromCart(${index})" title="Remove"></i>
            </div>
        </div>`;
    });

    container.innerHTML = html;
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
        const brand = card.getAttribute('data-brand').toLowerCase();
        const category = card.getAttribute('data-category').toLowerCase();

        if (name.includes(term) || brand.includes(term) || category.includes(term)) {
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
    executeCheckout('prepare');
}

function executeCheckout(action = 'finalize') {
    const customerName = document.getElementById('customerName').value;
    const customerPhone = document.getElementById('customerPhone').value;
    const paymentMethod = document.getElementById('paymentMethod').value;
    const btn = document.getElementById('checkoutBtn');

    // Loading state for finalization
    const originalText = btn.innerHTML;
    if (action === 'finalize') {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        btn.disabled = true;
    }

    const payload = {
        action: action,
        customer_name: customerName,
        customer_phone: customerPhone,
        payment_method: paymentMethod,
        items: cart,
        payment_ref: window.currentPaymentRef || null
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
                if (data.action === 'prepared') {
                    if (paymentMethod === 'UPI') {
                        showUpiModal(data.upi_url, data.bill_total, data.payment_ref);
                    } else {
                        // showCashModal(data.bill_total); // Optional: if you want a confirmation modal for cash
                        // Or just finalize directly if that's preferred
                        showCashModal(data.bill_total);
                    }
                    return;
                }

                // Success for finalize
                showToast("Bill Generated Successfully!", "success");

                // Open PDF if available
                if (data.bill_url) {
                    // Create a hidden anchor tag to force download
                    const link = document.createElement('a');
                    link.href = data.bill_url;
                    link.setAttribute('download', `${data.bill_no || 'bill'}.pdf`);
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }

                setTimeout(() => {
                    // Use global constant LEDGER_URL
                    window.location.href = LEDGER_URL;
                }, 2000);
            } else {
                alert('Error: ' + data.message);
                btn.innerHTML = originalText;
                btn.disabled = false;

                // Also reset modal buttons if any
                const modalConfirmBtn = document.getElementById('manualConfirmBtn');
                if (modalConfirmBtn) {
                    modalConfirmBtn.innerHTML = 'Confirm Payment';
                    modalConfirmBtn.disabled = false;
                }
                const cashBtn = document.querySelector('#cashModal .btn-confirm');
                if (cashBtn) {
                    cashBtn.innerHTML = 'Confirm Cash Received';
                    cashBtn.disabled = false;
                }
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('An error occurred during checkout');
            btn.innerHTML = originalText;
            btn.disabled = false;

            const modalConfirmBtn = document.getElementById('manualConfirmBtn');
            if (modalConfirmBtn) {
                modalConfirmBtn.innerHTML = 'Confirm Payment';
                modalConfirmBtn.disabled = false;
            }
            const cashBtn = document.querySelector('#cashModal .btn-confirm');
            if (cashBtn) {
                cashBtn.innerHTML = 'Confirm Cash Received';
                cashBtn.disabled = false;
            }
        });
}

// --- UPI QR Logic ---
let pollingInterval = null;
let pollFailCount = 0;
let pollingStartTime = 0;
const MAX_POLLING_TIME = 5 * 60 * 1000; // 5 minutes in ms

function showUpiModal(upiUrl, amount, paymentRef) {
    const modal = document.getElementById('upiModal');
    const qrImg = document.getElementById('upiQrImg');
    const loading = document.getElementById('qrLoading');
    const amountSpan = document.getElementById('modalAmount');

    // Store ref globally for finalizing
    window.currentPaymentRef = paymentRef;
    pollFailCount = 0;
    pollingStartTime = Date.now();

    amountSpan.innerText = '₹' + amount.toFixed(2);
    modal.style.display = 'flex';
    loading.style.display = 'flex';

    // Update UI steps
    updatePaymentStatusUI("Waiting for Payment...");

    const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(upiUrl)}`;

    qrImg.onload = () => {
        loading.style.display = 'none';
        startPaymentPolling(paymentRef);
    };

    qrImg.src = qrApiUrl;
}

function updatePaymentStatusUI(statusText, type = 'info') {
    const statusEl = document.getElementById('paymentStatusText');
    if (statusEl) {
        statusEl.innerText = statusText;
        statusEl.className = 'status-text ' + type;
    }
}

function startPaymentPolling(paymentRef) {
    if (pollingInterval) clearInterval(pollingInterval);
    console.log("Starting polling for:", paymentRef);

    pollingInterval = setInterval(() => {
        // Safety: check if modal is still open
        const modal = document.getElementById('upiModal');
        if (!modal || modal.style.display === 'none') {
            console.log("Modal closed, stopping polling");
            stopPolling();
            return;
        }

        // Safety: Timeout after 5 minutes
        if (Date.now() - pollingStartTime > MAX_POLLING_TIME) {
            console.log("Polling timed out");
            stopPolling();
            updatePaymentStatusUI("Polling Timed Out ❌", "error");
            showToast("Payment window expired. Please try again.", "error");
            return;
        }

        fetch(`/holi/api/check-payment-status/${paymentRef}`)
            .then(res => res.json())
            .then(data => {
                console.log("Payment Status:", data.status);
                pollFailCount = 0; // Reset fail count on success

                if (data.status === 'Paid') {
                    stopPolling();
                    updatePaymentStatusUI("Payment Confirmed ✅", "success");
                    showToast("Payment Detected!", "success");

                    setTimeout(() => {
                        updatePaymentStatusUI("Generating Bill...", "warning");
                        // Automatically generate bill
                        executeCheckout('finalize');
                        // Close modal after a short delay to let user see "Generating"
                        setTimeout(closeUpiModal, 1500);
                    }, 1000);
                } else if (data.status === 'Expired' || data.status === 'Cancelled') {
                    stopPolling();
                    updatePaymentStatusUI(data.status + " ❌", "error");
                    showToast(`Payment ${data.status}. Please try again.`, "error");
                } else if (data.status === 'Invalid') {
                    stopPolling();
                    updatePaymentStatusUI("Security Error ❌", "error");
                    showToast("Security verification failed. Reference tampered.", "error");
                } else {
                    updatePaymentStatusUI("Detecting Payment...", "info");
                }
            })
            .catch(err => {
                console.error("Polling error", err);
                pollFailCount++;
                if (pollFailCount > 5) {
                    console.log("Stopping polling due to too many failures");
                    stopPolling();
                    updatePaymentStatusUI("Connection Error ❌", "error");
                }
            });
    }, 5000);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

function closeUpiModal() {
    stopPolling();
    document.getElementById('upiModal').style.display = 'none';
}

function confirmUpiPayment() {
    // Manual fallback if auto-detection is slow
    // Removed the confirm() alert as per user request to generate bill directly
    stopPolling();

    // Mark payment as paid in DB first
    if (window.currentPaymentRef) {
        const confirmBtn = document.getElementById('manualConfirmBtn');
        const originalText = confirmBtn.innerHTML;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        confirmBtn.disabled = true;

        updatePaymentStatusUI("Confirming Receipt...", "warning");
        fetch(`/holi/api/verify-upi-payment/${window.currentPaymentRef}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    closeUpiModal();
                    executeCheckout('finalize');
                } else {
                    alert("Error confirming payment: " + data.message);
                }
            })
            .catch(err => {
                console.error("Manual confirm error", err);
                alert("Connection error during confirmation");
                confirmBtn.innerHTML = originalText;
                confirmBtn.disabled = false;
            });
    }
}

// --- Cash Modal Logic ---

function showCashModal(amount) {
    const modal = document.getElementById('cashModal');
    const amountSpan = document.getElementById('cashModalAmount');
    if (modal && amountSpan) {
        amountSpan.innerText = amount.toFixed(2);
        modal.style.display = 'flex';
    }
}

function closeCashModal() {
    document.getElementById('cashModal').style.display = 'none';
}

function confirmCashPayment() {
    const cashBtn = document.querySelector('#cashModal .btn-confirm');
    cashBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    cashBtn.disabled = true;

    // We don't close right away to show loading state
    executeCheckout('finalize');
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
