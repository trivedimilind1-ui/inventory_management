# SmartStock – Enterprise Supermarket Inventory Management System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%7C%20SQLite-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A complete, professional, full-stack supermarket inventory management system built with Python, Flask, SQLAlchemy, MySQL, Bootstrap 5, and Chart.js.

---

## 🌟 Key Features

### 1. 🔐 Role-Based Authentication & Authorization
- **Two Roles**:
  - **Store Manager (Admin)**: Full system access — Product CRUD, Category CRUD, Supplier CRUD, Financial Reports, Inventory Audits, Stock movements.
  - **Cashier (Staff)**: Restricted access — POS Billing Terminal, Stock inspection, Customer invoice generation.
- Secure password hashing using PBKDF2/SHA256 via Werkzeug.
- Protected routes using role decorators (`@admin_required`, `@login_required`).
- Auto session persistence with "Remember Me" support.

### 2. 📊 Main Dashboard & Visual Telemetry
- **Real-Time KPI Cards**:
  - Total Catalog Products
  - Total Active Categories
  - Total Units in Physical Stock
  - Total Inventory Valuation (₹)
  - Low Stock Alerts count
  - Out of Stock count
  - Completed Sales count
  - Today's Revenue (₹) and All-Time Gross Revenue
- **5 Dynamic Chart.js Analytics**:
  - 📈 Sales & Revenue Trajectory (Last 7 Days)
  - 🍩 Product Distribution by Category
  - 🏆 Top 5 Best-Selling Products by units and revenue
  - 🛡️ Stock Health Overview (In Stock, Low Stock, Out of Stock)
  - 📊 Monthly Revenue Performance
- **Live Stream**: Recent sales invoices, movement audit logs, and actionable low-stock warnings.

### 3. 📦 Product Management
- Complete CRUD operations with database transaction safety.
- Detailed metadata: Name, SKU, Barcode, Brand, Category, Supplier, Purchase Cost (₹), Selling Price (₹), Gross Margin %, Physical Stock, Minimum Stock Threshold, Unit of Measure, Expiry Date, and Description.
- Multi-field search (Name, SKU, Brand, Barcode).
- Category, Supplier, and Stock Status filters.
- Real-time sorting (Price asc/desc, Stock asc/desc, Name, Date added).
- Soft-delete mechanism preserving sales and billing transaction history (Rule #5).
- Product Detail modal with live margins and valuation.

### 4. 🏷️ Category Management
- Manage supermarket aisles and departments (Dairy, Beverages, Snacks, Grocery, Personal Care, Household, Bakery, Produce, Frozen, Stationery).
- Icon customization using Bootstrap Icons.
- Live calculation of active products within each category.
- **Safety Lock**: Prevents deletion of categories containing active products.

### 5. 📦 Stock Tracking & Inventory Movements
- Current stock overview with status badges.
- **Stock IN (Restock)**: Fast inward receipt modal recording delivery challans and vendor PO numbers.
- **Stock Adjustments**: Write-offs for damaged goods, expired products, and physical shelf count audits.
- **Strict Non-Negative Stock Rule**: System blocks any deduction exceeding on-hand inventory.
- Full audit log of all historical stock transitions (Timestamp, Delta, Previous Qty, New Qty, Reason, Logged By).

### 6. 💳 Supermarket POS Billing Terminal
- Interactive split-screen POS terminal designed for high checkout throughput.
- Instant search and category filter tabs.
- **Hardware Barcode Scanner Support**: Press Enter or scan to immediately add to cart.
- Live cart calculations:
  - Quantity increment/decrement buttons with inventory boundary checks.
  - Configurable GST/tax rate (Default: 5%).
  - Flat discount application.
  - Automatic subtotal, tax amount, and net grand total.
- Payment modes: **Cash**, **Credit/Debit Card**, and **UPI / QR**.
- **Atomic Database Transaction**: Verifies inventory lock, inserts sale, inserts sale items, deducts stock, and logs movement within a single atomic commit.
- **Printable Supermarket Tax Invoice**:
  - Formatted for standard 80mm POS thermal receipt printers and A4 desktop printing.
  - Complete with store branding, GSTIN, address, customer details, line items, tax breakdown, barcode representation, and return policy.

### 7. 🚚 Supplier Management
- Track wholesale distributors and procurement partners (Amul, Tata Consumer, ITC, HUL, Nestlé).
- Store contact details: Representative name, company, phone, email, address, and GSTIN.
- View dedicated supplier catalogs showing all products supplied by a vendor.

### 8. 📈 Reports & Financial Analytics
- Date Range Filter: Today, Last 7 Days, Last 30 Days, This Year, or Custom Date Picker.
- Financial Metrics: Total Orders, Gross Revenue, Gross Profit (Revenue − Cost of Goods Sold), Profit Margin %, Average Order Value (AOV).
- Potential Gross Profit estimation on currently held inventory.
- Top 5 Best-Selling Products vs Slow-Moving Inventory.
- Low-Stock Reorder Priority Report with calculated deficit and estimated replenishment cost.
- **1-Click Downloadable CSV Reports**:
  - `smartstock_sales_report.csv`
  - `smartstock_inventory_valuation.csv`
  - `smartstock_stock_movements.csv`

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12+, Flask 3.1, Flask-SQLAlchemy, Flask-Login, PyMySQL, python-dotenv
- **Database**: MySQL 8.0+ / SQLite 3 (automatic zero-config local fallback)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4
- **Testing**: Python `unittest` test suite verifying all 15 core workflows end-to-end.

---

## 🗄️ Database Architecture

The relational schema comprises 10 normalized tables:

```
users ───────────< sales ───────────< sale_items >─────────── products
  │                 │                                            │
  │                 │                                            │
  └───────< activity_logs                                        ├────< stock_movements
                                                                 │
                                     categories ────────< products >──────── suppliers
```

1. **`users`**: id, username, email, password_hash, full_name, role (`admin`/`staff`), phone, is_active, timestamps.
2. **`categories`**: id, name, description, icon, is_active, timestamps.
3. **`suppliers`**: id, name, company_name, phone, email, address, gst_number, is_active, timestamps.
4. **`products`**: id, name, sku, barcode, category_id, supplier_id, brand, purchase_price, selling_price, quantity, min_stock_level, unit, expiry_date, description, is_active, timestamps.
5. **`sales`**: id, invoice_no, user_id, customer_name, customer_phone, subtotal, tax_rate, tax_amount, discount_amount, total_amount, payment_method, status, notes, created_at.
6. **`sale_items`**: id, sale_id, product_id, product_name, sku, unit_cost, unit_price, quantity, line_total, line_profit, created_at.
7. **`stock_movements`**: id, product_id, movement_type (`in`/`out`/`sale`/`adjustment`/`return`), quantity, previous_quantity, new_quantity, reason, reference_id, user_id, created_at.
8. **`purchase_orders`**: id, po_number, supplier_id, user_id, order_date, expected_date, total_amount, status, notes, timestamps.
9. **`purchase_order_items`**: id, po_id, product_id, quantity, unit_price, line_total, received_quantity.
10. **`activity_logs`**: id, user_id, action, entity_type, entity_id, details, ip_address, created_at.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone & Setup
```bash
git clone https://github.com/trivedimilind1-ui/inventory_management.git
cd inventory_management
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

To connect to a **MySQL** database, update `.env`:
```env
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/smartstock
```
*(If no MySQL URL is set, SmartStock automatically initializes a local SQLite database `smartstock.db` with full sample data out of the box).*

### 4. Run Application
```bash
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser!

---

## 🔑 Default Demo Accounts

The database comes pre-seeded with 35+ realistic supermarket items (Amul Butter, Tata Salt, Maggi, Aashirvaad Atta, Surf Excel, etc.) across 10 categories, 5 suppliers, and 15 historical sales.

| Role | Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Store Manager** | `admin` | `admin123` | Full access (Products, Categories, Suppliers, Reports, Audits) |
| **Cashier** | `staff` | `staff123` | POS Billing Terminal, Stock view, Receipt printing |

*(Tip: On the login screen, click the "Admin" or "Staff" pill to auto-fill credentials instantly).*

---

## 🧪 Automated Testing

Execute the complete end-to-end test suite:
```bash
python -m unittest tests/test_app.py
```
Verifies all 15 operational workflows:
1. User registration, password hashing, and session authentication.
2. Category creation, editing, deletion, and product foreign key protection.
3. Product addition with unique SKU validation.
4. Product editing and price updates.
5. Soft-delete safeguarding sales integrity.
6. Stock IN restocking with delivery references.
7. POS checkout and payment recording.
8. Automatic inventory deduction.
9. Sales history archiving.
10. Tax invoice rendering with GST calculations.
11. Dashboard metric queries and Chart.js endpoints.
12. Financial report calculations and CSV export generation.
13. Minimum stock threshold and out-of-stock warning triggers.
14. Role-based authorization rules.
15. Database persistence across transactions.

---

## ☁️ Deployment

### Vercel Deployment
This repository is configured with `vercel.json` and a serverless WSGI handler in `api/index.py`.
```bash
vercel --prod
```

### Gunicorn (Linux / Render / Railway)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 📄 License
This project is licensed under the MIT License.
