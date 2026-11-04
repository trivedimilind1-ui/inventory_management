-- ==========================================================
-- SMARTSTOCK SUPERMARKET - RELATIONAL DATABASE SCHEMA (MySQL)
-- ==========================================================

CREATE DATABASE IF NOT EXISTS `smartstock` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `smartstock`;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Users Table
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(80) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(120) NOT NULL,
    `role` VARCHAR(20) NOT NULL DEFAULT 'staff',
    `phone` VARCHAR(20) NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Categories Table
DROP TABLE IF EXISTS `categories`;
CREATE TABLE `categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `icon` VARCHAR(50) NOT NULL DEFAULT 'bi-tag',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Suppliers Table
DROP TABLE IF EXISTS `suppliers`;
CREATE TABLE `suppliers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(120) NOT NULL,
    `company_name` VARCHAR(150) NOT NULL,
    `phone` VARCHAR(30) NOT NULL,
    `email` VARCHAR(120) NULL,
    `address` TEXT NULL,
    `gst_number` VARCHAR(50) NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_suppliers_company` (`company_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Products Table
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL,
    `sku` VARCHAR(64) NOT NULL UNIQUE,
    `barcode` VARCHAR(64) NULL,
    `category_id` INT NOT NULL,
    `supplier_id` INT NULL,
    `brand` VARCHAR(100) NOT NULL DEFAULT 'Generic',
    `purchase_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `selling_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `quantity` INT NOT NULL DEFAULT 0,
    `min_stock_level` INT NOT NULL DEFAULT 10,
    `unit` VARCHAR(20) NOT NULL DEFAULT 'pcs',
    `expiry_date` DATE NULL,
    `description` TEXT NULL,
    `image_url` VARCHAR(255) NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_products_category` FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_products_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers`(`id`) ON DELETE SET NULL,
    INDEX `idx_products_sku` (`sku`),
    INDEX `idx_products_name` (`name`),
    INDEX `idx_products_qty` (`quantity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Sales Table
DROP TABLE IF EXISTS `sales`;
CREATE TABLE `sales` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `invoice_no` VARCHAR(64) NOT NULL UNIQUE,
    `user_id` INT NULL,
    `customer_name` VARCHAR(100) NOT NULL DEFAULT 'Walk-in Customer',
    `customer_phone` VARCHAR(20) NULL,
    `subtotal` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `tax_rate` DECIMAL(5,2) NOT NULL DEFAULT 5.00,
    `tax_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `discount_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `total_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `payment_method` VARCHAR(20) NOT NULL DEFAULT 'cash',
    `status` VARCHAR(20) NOT NULL DEFAULT 'completed',
    `notes` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_sales_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    INDEX `idx_sales_invoice` (`invoice_no`),
    INDEX `idx_sales_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Sale Items Table
DROP TABLE IF EXISTS `sale_items`;
CREATE TABLE `sale_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `sale_id` INT NOT NULL,
    `product_id` INT NULL,
    `product_name` VARCHAR(150) NOT NULL,
    `sku` VARCHAR(64) NOT NULL,
    `unit_cost` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `unit_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `quantity` INT NOT NULL DEFAULT 1,
    `line_total` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `line_profit` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_sale_items_sale` FOREIGN KEY (`sale_id`) REFERENCES `sales`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_sale_items_product` FOREIGN KEY (`product_id`) REFERENCES `products`(`id`) ON DELETE SET NULL,
    INDEX `idx_sale_items_sale_id` (`sale_id`),
    INDEX `idx_sale_items_product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Stock Movements Table
DROP TABLE IF EXISTS `stock_movements`;
CREATE TABLE `stock_movements` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `product_id` INT NOT NULL,
    `movement_type` VARCHAR(30) NOT NULL,
    `quantity` INT NOT NULL,
    `previous_quantity` INT NOT NULL,
    `new_quantity` INT NOT NULL,
    `reason` VARCHAR(255) NULL,
    `reference_id` VARCHAR(100) NULL,
    `user_id` INT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_movements_product` FOREIGN KEY (`product_id`) REFERENCES `products`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_movements_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    INDEX `idx_movements_product` (`product_id`),
    INDEX `idx_movements_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Purchase Orders Table
DROP TABLE IF EXISTS `purchase_orders`;
CREATE TABLE `purchase_orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `po_number` VARCHAR(64) NOT NULL UNIQUE,
    `supplier_id` INT NOT NULL,
    `user_id` INT NULL,
    `order_date` DATE NOT NULL,
    `expected_date` DATE NULL,
    `total_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `notes` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_po_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers`(`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_po_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Purchase Order Items Table
DROP TABLE IF EXISTS `purchase_order_items`;
CREATE TABLE `purchase_order_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `po_id` INT NOT NULL,
    `product_id` INT NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `unit_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `line_total` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `received_quantity` INT NOT NULL DEFAULT 0,
    CONSTRAINT `fk_poi_order` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_poi_product` FOREIGN KEY (`product_id`) REFERENCES `products`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Activity Logs Table
DROP TABLE IF EXISTS `activity_logs`;
CREATE TABLE `activity_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `action` VARCHAR(50) NOT NULL,
    `entity_type` VARCHAR(50) NOT NULL,
    `entity_id` VARCHAR(50) NULL,
    `details` VARCHAR(255) NOT NULL,
    `ip_address` VARCHAR(45) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_activity_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    INDEX `idx_activity_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
