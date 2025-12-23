-- Tabel Toko
CREATE TABLE IF NOT EXISTS stores (
    store_id SERIAL PRIMARY KEY,
    store_name VARCHAR(100),
    location VARCHAR(100)
);

-- Tabel Produk
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    unit_cost NUMERIC(12,2),
    price NUMERIC(12,2),         
    stock INT DEFAULT 0,
    safety_stock INT DEFAULT 10,
    eoq INT DEFAULT 2,
    updated_at TIMESTAMP DEFAULT NOW(),
    is_event BOOLEAN DEFAULT FALSE
);

-- Tabel Events
CREATE TABLE IF NOT EXISTS events (
    event_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    start_date DATE,
    end_date DATE
);

-- Tabel Transaksi 
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id SERIAL PRIMARY KEY,
    store_id INT REFERENCES stores(store_id),
    product_id INT REFERENCES products(product_id),
    qty INT,
    price NUMERIC(12,2),
    payment_method VARCHAR(20), 
    created_at TIMESTAMP
);

-- Tabel Supplier
CREATE TABLE IF NOT EXISTS supplier (
    supplier_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    lead_time_days INT,
    min_order_qty INT,
    pack_size INT,
    shipping_options TEXT
);

-- Tabel Promo
CREATE TABLE IF NOT EXISTS promo (
    promo_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    start_date DATE,
    end_date DATE,
    discount_percent NUMERIC(5,2),
    description TEXT
);

-- Tabel Log Restock
CREATE TABLE IF NOT EXISTS restock_log (
    log_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    restocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    restocked_to INT
);

-- Tabel Staging Transactions
CREATE TABLE IF NOT EXISTS staging_transactions (
    temp_id VARCHAR(50),
    store_id INT,
    product_id INT,
    qty INT,
    price NUMERIC(12,2),
    payment_method VARCHAR(20),
    trx_date TIMESTAMP
);

-- Inisialisasi Data Awal
-- Stores
INSERT INTO stores (store_id, store_name, location) 
VALUES (1, 'BUTIK LAYLAY', 'Malang') 
ON CONFLICT (store_id) DO NOTHING;

-- Products (Barang Harian)
INSERT INTO products (product_id, name, category, price, unit_cost, stock, is_event)
VALUES
(1, 'Kaos Polos', 'Fashion', 50000, 30000, 100, FALSE),
(2, 'Celana Jeans', 'Fashion', 150000, 90000, 80, FALSE),
(3, 'Jaket Hoodie', 'Fashion', 200000, 120000, 60, FALSE),
(4, 'Sepatu Sneakers', 'Fashion', 300000, 185475, 50, FALSE),
(5, 'Topi', 'Aksesoris', 75000, 45625, 120, FALSE)
ON CONFLICT (product_id) DO NOTHING;

-- Products (Barang Event Natal)
INSERT INTO products (product_id, name, category, price, unit_cost, stock, is_event)
VALUES
(101, 'Sweater Natal', 'Event Natal', 250000, 180000, 50, TRUE),
(102, 'Celana Chino', 'Event Natal', 75000, 50000, 100, TRUE),
(103, 'Kemeja Kotak', 'Event Natal', 150000, 100000, 200, TRUE)
ON CONFLICT (product_id) DO NOTHING;

-- Events
INSERT INTO events (name, start_date, end_date) VALUES 
('NATARU SALE', '2025-12-10', '2025-12-31')
ON CONFLICT DO NOTHING;

-- Supplier
INSERT INTO supplier (name, lead_time_days, min_order_qty, pack_size, shipping_options) 
VALUES 
('PT. Tekstil Jaya', 3, 50, 10, 'Trucking'),
('CV. Malang Gaspol', 5, 20, 5, 'Air Freight')
ON CONFLICT DO NOTHING;

-- Promo
INSERT INTO promo (product_id, start_date, end_date, discount_percent, description)
VALUES
(101, '2025-12-10', '2025-12-25', 20.00, 'Diskon Sweater Natal')
ON CONFLICT DO NOTHING;