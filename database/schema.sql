-- SQL Schema for Shop Project (Supabase / PostgreSQL)

-- 0. Cleanup (Drop tables in reverse dependency order)
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS bill_items CASCADE;
DROP TABLE IF EXISTS bills CASCADE;
DROP TABLE IF EXISTS products CASCADE;

-- 1. Products Table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    store_name TEXT DEFAULT 'Holi Store',
    product_name TEXT,
    brand TEXT,
    category TEXT,
    price_quantity TEXT,
    product_unit TEXT,
    cost_price DECIMAL,
    base_price DECIMAL,
    tax_percent DECIMAL,
    tax_amount DECIMAL,
    profit_margin DECIMAL,
    sell_price DECIMAL,
    stock INT DEFAULT 0,
    sold_stock INT DEFAULT 0,
    stock_status TEXT,
    product_status TEXT,
    last_updated_quantity INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bills Table
CREATE TABLE IF NOT EXISTS bills (
    bill_id SERIAL PRIMARY KEY,
    bill_no TEXT UNIQUE,
    store_name TEXT,
    total_product INT,
    total_quantity INT,
    subtotal_amount DECIMAL,
    total_tax_amount DECIMAL,
    bill_total DECIMAL,
    payment_status TEXT,
    bill_status TEXT,
    payment_id TEXT UNIQUE, -- Stores payment_reference, unique to prevent duplicate bills
    payment_method TEXT,
    bill_url TEXT, -- Link to generated PDF bill
    customer_name TEXT,
    customer_phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bill_date ON bills(created_at);

-- 3. Bill Items Table (Normalised structure)
CREATE TABLE IF NOT EXISTS bill_items (
    bill_item_id SERIAL PRIMARY KEY,
    bill_id INT REFERENCES bills(bill_id),
    product_id INT, -- Added for reference
    product_name TEXT,
    quantity INT,
    product_unit TEXT,
    base_price DECIMAL,
    tax_percent DECIMAL,
    tax_amount DECIMAL,
    final_price DECIMAL,
    total_price DECIMAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_product_id ON bill_items(product_id);

-- 4. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    bill_id INT REFERENCES bills(bill_id),
    store_name TEXT,
    payment_method TEXT CHECK (payment_method IN ('Cash', 'Card', 'UPI', 'NetBanking')),
    payment_type TEXT CHECK (payment_type IN ('Full', 'Partial')),
    transaction_id TEXT,
    payment_reference TEXT,
    paid_amount DECIMAL,
    remaining_amount DECIMAL,
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

-- 5. Atomic Functions (Run these in Supabase SQL Editor)
-- CREATE OR REPLACE FUNCTION decrement_stock_if_enough(p_id INT, p_qty INT)
-- RETURNS BOOLEAN AS $$
-- BEGIN
--   UPDATE products
--   SET stock = stock - p_qty,
--       sold_stock = sold_stock + p_qty
--   WHERE product_id = p_id AND stock >= p_qty;
--   RETURN FOUND;
-- END;
-- $$ LANGUAGE plpgsql;
