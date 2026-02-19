-- SQL Schema for Shop Project (Supabase / PostgreSQL)

-- 1. Sellers Table
CREATE TABLE IF NOT EXISTS sellers (
    seller_id SERIAL PRIMARY KEY,
    seller_name TEXT NOT NULL,
    store_name TEXT NOT NULL,
    store_type TEXT,
    seller_phone TEXT NOT NULL,
    seller_email TEXT NOT NULL,
    pan_number TEXT,
    gst_number TEXT,
    store_address TEXT,
    store_city TEXT,
    store_state TEXT,
    store_pincode TEXT,
    bank_account_no TEXT,
    ifsc_code TEXT,
    upi_id TEXT,
    seller_status TEXT CHECK (seller_status IN ('Active', 'Inactive', 'Blocked')),
    join_date DATE DEFAULT CURRENT_DATE,
    last_login TIMESTAMP,
    total_product INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Products Table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY, -- Using SERIAL for auto-increment
    id INT UNIQUE, -- Keeping original ID for compatibility if needed, else product_id can replace it
    store_name TEXT,
    product_name TEXT NOT NULL,
    product_category TEXT,
    product_brand TEXT,
    product_weight DECIMAL,
    product_unit TEXT,
    price_quantity TEXT,
    base_price DECIMAL,
    cost_price DECIMAL,
    tax_percent DECIMAL,
    tax_amount DECIMAL,
    profit_margin DECIMAL,
    final_price DECIMAL,
    stock INT DEFAULT 0, -- mapped from 'stock' in JSON
    price DECIMAL, -- mapped from 'price' in JSON
    image TEXT, -- mapped from 'image' in JSON
    offer_price DECIMAL,
    product_quantity INT,
    sold_quantity INT DEFAULT 0,
    stock_status TEXT CHECK (stock_status IN ('InStock', 'OutOfStock')),
    last_updated_quantity INT,
    seller_id INT REFERENCES sellers(seller_id),
    product_status TEXT,
    name TEXT, -- mapped from 'name' in JSON
    category TEXT, -- mapped from 'category' in JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Bills Table
CREATE TABLE IF NOT EXISTS bills (
    bill_id SERIAL PRIMARY KEY,
    id INT UNIQUE,
    bill_no TEXT,
    seller_id INT REFERENCES sellers(seller_id),
    store_name TEXT,
    total_items INT,
    total_quantity INT,
    subtotal_amount DECIMAL,
    total_tax_amount DECIMAL,
    bill_total DECIMAL,
    product_name TEXT, -- Denormalized for simple bill structure
    quantity INT,
    price DECIMAL,
    total DECIMAL,
    date DATE,
    payment_status TEXT CHECK (payment_status IN ('Paid', 'Pending')),
    bill_status TEXT CHECK (bill_status IN ('Completed', 'Cancelled')),
    payment_id INT,
    bill_date DATE,
    bill_time TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Bill Items Table (Normalised structure)
CREATE TABLE IF NOT EXISTS bill_items (
    bill_item_id SERIAL PRIMARY KEY,
    bill_id INT REFERENCES bills(bill_id),
    product_id INT REFERENCES products(product_id),
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

-- 5. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    bill_id INT REFERENCES bills(bill_id),
    payment_method TEXT CHECK (payment_method IN ('Cash', 'Card', 'UPI', 'NetBanking')),
    payment_type TEXT CHECK (payment_type IN ('Full', 'Partial')),
    transaction_id TEXT,
    payment_reference TEXT,
    paid_amount DECIMAL,
    remaining_amount DECIMAL,
    payment_status TEXT CHECK (payment_status IN ('Paid', 'Pending', 'Failed', 'Refunded')),
    payment_date DATE,
    payment_time TIME,
    received_by TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
