-- Database Schema: ecommerce_system
-- Generated for POSTGRESQL
-- Tables: 5

-- Table: customers
-- Customer information
CREATE TABLE customers (
    id INTEGER NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    PRIMARY KEY (id)
);

-- Table: categories
-- Product categories
CREATE TABLE categories (
    id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER,
    PRIMARY KEY (id)
);

-- Table: products
-- Product catalog
CREATE TABLE products (
    id INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category_id INTEGER,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    PRIMARY KEY (id)
);

-- Table: orders
-- Customer orders
CREATE TABLE orders (
    id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    order_date TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    shipping_address TEXT,
    billing_address TEXT,
    PRIMARY KEY (id)
);

-- Table: order_items
-- Individual items within orders
CREATE TABLE order_items (
    id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE categories ADD FOREIGN KEY (parent_id) REFERENCES categories(id);
ALTER TABLE products ADD FOREIGN KEY (category_id) REFERENCES categories(id);
ALTER TABLE orders ADD FOREIGN KEY (customer_id) REFERENCES customers(id);
ALTER TABLE order_items ADD FOREIGN KEY (order_id) REFERENCES orders(id);
ALTER TABLE order_items ADD FOREIGN KEY (product_id) REFERENCES products(id);