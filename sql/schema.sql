PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS regions (
    region_id TEXT PRIMARY KEY,
    region_name TEXT NOT NULL,
    macro_region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    region_id TEXT NOT NULL REFERENCES regions(region_id),
    signup_date TEXT NOT NULL,
    customer_segment TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL CHECK (unit_price > 0),
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0)
);

CREATE TABLE IF NOT EXISTS sellers (
    seller_id TEXT PRIMARY KEY,
    seller_name TEXT NOT NULL,
    region_id TEXT NOT NULL REFERENCES regions(region_id),
    hire_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    sale_date TEXT NOT NULL,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    seller_id TEXT NOT NULL REFERENCES sellers(seller_id),
    region_id TEXT NOT NULL REFERENCES regions(region_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price > 0),
    discount_pct REAL NOT NULL CHECK (discount_pct BETWEEN 0 AND 1),
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
    gross_revenue REAL NOT NULL,
    discount_amount REAL NOT NULL,
    net_revenue REAL NOT NULL,
    estimated_cost REAL NOT NULL,
    estimated_margin REAL NOT NULL,
    margin_pct REAL
);

CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_region ON sales(region_id);
CREATE INDEX IF NOT EXISTS idx_sales_order ON sales(order_id);
