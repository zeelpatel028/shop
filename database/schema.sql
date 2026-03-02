-- SQL Schema for Shop Project (Production PostgreSQL)

-- 2. Products Table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    store_name TEXT DEFAULT 'Holi Store',
    product_name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    price_quantity TEXT,
    product_unit TEXT,
    cost_price DECIMAL(12, 2),
    base_price DECIMAL(12, 2),
    tax_percent DECIMAL(5, 2),
    tax_amount DECIMAL(12, 2),
    profit_margin DECIMAL(12, 2),
    sell_price DECIMAL(12, 2),
    stock INT DEFAULT 0,
    sold_stock INT DEFAULT 0,
    stock_status TEXT,
    product_status TEXT DEFAULT 'Active',
    last_updated_quantity INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_name ON products(product_name);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

-- 3. Bills Table
CREATE TABLE IF NOT EXISTS bills (
    bill_id SERIAL PRIMARY KEY,
    bill_no TEXT UNIQUE NOT NULL,
    store_name TEXT,
    total_product INT,
    total_quantity INT,
    subtotal_amount DECIMAL(12, 2),
    total_tax_amount DECIMAL(12, 2),
    bill_total DECIMAL(12, 2),
    payment_status TEXT,
    bill_status TEXT DEFAULT 'Final',
    payment_id TEXT UNIQUE, -- Stores payment_reference, unique to prevent duplicate bills
    payment_method TEXT,
    bill_url TEXT, -- Link to generated PDF bill
    customer_name TEXT,
    customer_phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bill_date ON bills(created_at);
CREATE INDEX IF NOT EXISTS idx_bill_customer_phone ON bills(customer_phone);

-- 4. Bill Items Table (Normalised structure)
CREATE TABLE IF NOT EXISTS bill_items (
    bill_item_id SERIAL PRIMARY KEY,
    bill_id INT REFERENCES bills(bill_id) ON DELETE CASCADE,
    product_id INT, -- Added for reference
    product_name TEXT,
    quantity INT,
    product_unit TEXT,
    base_price DECIMAL(12, 2),
    tax_percent DECIMAL(5, 2),
    tax_amount DECIMAL(12, 2),
    final_price DECIMAL(12, 2),
    total_price DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bill_items_bill_id ON bill_items(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_items_product_id ON bill_items(product_id);

-- 5. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    bill_id INT REFERENCES bills(bill_id) ON DELETE SET NULL,
    store_name TEXT,
    payment_method TEXT CHECK (payment_method IN ('Cash', 'Card', 'UPI', 'NetBanking')),
    payment_type TEXT CHECK (payment_type IN ('Full', 'Partial')),
    transaction_id TEXT,
    payment_reference TEXT,
    paid_amount DECIMAL(12, 2),
    remaining_amount DECIMAL(12, 2),
    payment_status TEXT CHECK (payment_status IN ('Paid', 'Pending', 'Failed', 'Refunded', 'Expired')),
    received_by TEXT,
    notes TEXT,
    bill_url TEXT,
    is_bill_generated BOOLEAN DEFAULT FALSE,
    payment_expire_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_ref ON payments(payment_reference);
CREATE INDEX IF NOT EXISTS idx_payment_bill_id ON payments(bill_id);
 
-- 6. Customer Table
CREATE TABLE IF NOT EXISTS customer (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phone_no TEXT UNIQUE NOT NULL,
    address TEXT,
    padin_amount_last DECIMAL(12, 2) DEFAULT 0,
    padin_amount_total DECIMAL(12, 2) DEFAULT 0,
    panding_bill_count INT DEFAULT 0,
    all_bill_count INT DEFAULT 0,
    last_payment_date TIMESTAMP,
    status TEXT DEFAULT 'Active',
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customer_phone ON customer(phone_no);

-- 7. Credit Bill Table
CREATE TABLE IF NOT EXISTS credit_bill (
    id SERIAL PRIMARY KEY,
    c_id INT REFERENCES customer(id) ON DELETE CASCADE,
    bill_id INT REFERENCES bills(bill_id) ON DELETE SET NULL,
    bill_url TEXT,
    total_price DECIMAL(12, 2),
    paid_amount DECIMAL(12, 2) DEFAULT 0,
    remaining_amount DECIMAL(12, 2),
    bill_discreption TEXT, -- all item and qun and price
    bill_status TEXT,
    payment_status TEXT,
    payment_method TEXT,
    payment_date TIMESTAMP,
    created_date TEXT,
    created_time TEXT,
    approved_date TEXT,
    approved_time TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_credit_bill_cid ON credit_bill(c_id);
CREATE INDEX IF NOT EXISTS idx_credit_bill_id ON credit_bill(bill_id);

-- 8. Seller Table
CREATE TABLE IF NOT EXISTS seller (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    shope_name TEXT,
    gst_no TEXT,
    email TEXT,
    phone TEXT UNIQUE NOT NULL,
    pan_no TEXT,
    address TEXT,
    city TEXT,
    total_products INT DEFAULT 0,
    total_orders INT DEFAULT 0,
    pending_orders INT DEFAULT 0,
    return_total INT DEFAULT 0,
    complete_orders INT DEFAULT 0,
    bank_account_holder_name TEXT,
    bank_account_number TEXT,
    ifsc_code TEXT,
    upi_id TEXT,
    account_status TEXT DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_seller_phone ON seller(phone);

-- 9. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    bill_item_id INT REFERENCES bill_items(bill_item_id) ON DELETE SET NULL,
    seller_id INT REFERENCES seller(id) ON DELETE CASCADE,
    store_name TEXT,
    total_product INT,
    total_quantity INT,
    subtotal_amount DECIMAL(12, 2),
    total_tax_amount DECIMAL(12, 2),
    bill_total DECIMAL(12, 2),
    payment_status TEXT,
    bill_status TEXT DEFAULT 'Final',
    payment_id TEXT UNIQUE, -- Stores payment_reference, unique to prevent duplicate bills
    payment_method TEXT,
    bill_url TEXT, -- Link to generated PDF bill
    order_status TEXT DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_seller_id ON orders(seller_id);
