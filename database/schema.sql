-- SQL Schema for Shop Project (Production PostgreSQL)

-- 0. Cleanup (Drop tables in reverse dependency order)
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS bill_items CASCADE;
DROP TABLE IF EXISTS bills CASCADE;
DROP TABLE IF EXISTS products CASCADE;


-- 2. Products Table
CREATE TABLE products (
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

CREATE INDEX idx_products_name ON products(product_name);
CREATE INDEX idx_products_category ON products(category);

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

CREATE INDEX idx_bill_date ON bills(created_at);
CREATE INDEX idx_bill_customer_phone ON bills(customer_phone);

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

CREATE INDEX idx_bill_items_bill_id ON bill_items(bill_id);
CREATE INDEX idx_bill_items_product_id ON bill_items(product_id);

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

CREATE INDEX idx_payment_ref ON payments(payment_reference);
CREATE INDEX idx_payment_bill_id ON payments(bill_id);
