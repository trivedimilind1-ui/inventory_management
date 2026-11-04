import unittest
import json
from decimal import Decimal
from datetime import date
from app import create_app
from config import Config
from models import db, User, Category, Product, Supplier, Sale, SaleItem, StockMovement

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class SmartStockFullSystemTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_workflow_01_seed_and_auth(self):
        """1. Register and log in workflow"""
        # Test admin user exists from seed
        admin = User.query.filter_by(username='admin').first()
        self.assertIsNotNone(admin)
        self.assertTrue(admin.check_password('admin123'))
        self.assertTrue(admin.is_admin)

        # Test login
        res = self.client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Supermarket Dashboard', res.data)

        # Log out before registering new user
        self.client.get('/auth/logout')

        # Test new user registration
        res_reg = self.client.post('/auth/register', data={
            'username': 'cashier_raj',
            'email': 'raj@smartstock.in',
            'full_name': 'Rajesh Kumar',
            'phone': '+91 99999 88888',
            'role': 'staff',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)

        new_user = User.query.filter_by(username='cashier_raj').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.role, 'staff')

    def test_workflow_02_category_crud(self):
        """2. Add, Edit, Delete Category and product constraint protection"""
        # Login as Admin
        self.client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'})

        # Add Category
        res = self.client.post('/categories/add', data={
            'name': 'Gourmet Chocolates',
            'description': 'Imported dark and milk chocolates',
            'icon': 'bi-gift'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        cat = Category.query.filter_by(name='Gourmet Chocolates').first()
        self.assertIsNotNone(cat)

        # Edit Category
        res_edit = self.client.post(f'/categories/edit/{cat.id}', data={
            'name': 'Artisanal Chocolates',
            'description': 'Premium Swiss and Belgian chocolates',
            'icon': 'bi-gift-fill'
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)
        self.assertEqual(cat.name, 'Artisanal Chocolates')

        # Delete Category without products
        res_del = self.client.post(f'/categories/delete/{cat.id}', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertFalse(cat.is_active)

    def test_workflow_03_04_05_product_crud(self):
        """3, 4, 5. Add, Edit, and Delete Product"""
        self.client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'})
        cat = Category.query.first()
        sup = Supplier.query.first()

        # 3. Add Product
        res_add = self.client.post('/products/add', data={
            'name': 'Organic Almond Milk 1L',
            'sku': 'BEV-ALM-999',
            'barcode': '8901234567890',
            'brand': 'PurePlant',
            'category_id': cat.id,
            'supplier_id': sup.id,
            'purchase_price': 180.00,
            'selling_price': 240.00,
            'quantity': 25,
            'min_stock_level': 10,
            'unit': 'ltr',
            'expiry_date': '2027-12-31',
            'description': 'Dairy-free unsweetened almond drink'
        }, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)

        prod = Product.query.filter_by(sku='BEV-ALM-999').first()
        self.assertIsNotNone(prod)
        self.assertEqual(prod.quantity, 25)

        # 4. Edit Product
        res_edit = self.client.post(f'/products/edit/{prod.id}', data={
            'name': 'Organic Almond Milk 1L (Fortified)',
            'sku': 'BEV-ALM-999',
            'barcode': '8901234567890',
            'brand': 'PurePlant Premium',
            'category_id': cat.id,
            'supplier_id': sup.id,
            'purchase_price': 190.00,
            'selling_price': 260.00,
            'min_stock_level': 12,
            'unit': 'ltr',
            'expiry_date': '2027-12-31',
            'description': 'Fortified with Vitamin B12 and Calcium'
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)
        self.assertEqual(prod.selling_price, Decimal('260.00'))

        # 5. Delete Product (Soft delete preserves historical integrity)
        res_del = self.client.post(f'/products/delete/{prod.id}', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertFalse(prod.is_active)

    def test_workflow_06_stock_in_and_adjustments(self):
        """6. Add stock and verify movement tracking and non-negative rule"""
        self.client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'})
        prod = Product.query.filter(Product.is_active == True, Product.quantity > 10).first()
        initial_qty = prod.quantity

        # Add Stock (Stock IN)
        res_in = self.client.post('/inventory/add-stock', data={
            'product_id': prod.id,
            'quantity': 30,
            'reason': 'Vendor delivery test',
            'reference_id': 'PO-TEST-101'
        }, follow_redirects=True)
        self.assertEqual(res_in.status_code, 200)
        self.assertEqual(prod.quantity, initial_qty + 30)

        # Verify Stock Movement logged
        mov = StockMovement.query.filter_by(reference_id='PO-TEST-101').first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.movement_type, 'in')
        self.assertEqual(mov.quantity, 30)
        self.assertEqual(mov.previous_quantity, initial_qty)
        self.assertEqual(mov.new_quantity, initial_qty + 30)

        # Test Non-Negative Stock Rule on reduction
        res_neg = self.client.post('/inventory/adjust', data={
            'product_id': prod.id,
            'adjustment_type': 'reduction',
            'quantity': prod.quantity + 50,  # Exceeds available quantity
            'reason': 'Damaged in transit'
        }, follow_redirects=True)
        self.assertIn(b'Stock cannot be negative', res_neg.data)

    def test_workflow_07_08_09_10_sale_and_billing(self):
        """7, 8, 9, 10. Sell product, verify stock decreases, sale logged, and invoice generated"""
        self.client.post('/auth/login', data={'username': 'staff', 'password': 'staff123'})
        prod = Product.query.filter(Product.is_active == True, Product.quantity >= 10).first()
        initial_qty = prod.quantity
        sale_qty = 3

        # POS Checkout JSON POST
        checkout_payload = {
            'customer_name': 'Aarav Mehta',
            'customer_phone': '+91 98765 43210',
            'payment_method': 'upi',
            'tax_rate': 5.0,
            'discount_amount': 15.0,
            'items': [
                {'product_id': prod.id, 'quantity': sale_qty}
            ]
        }

        res_checkout = self.client.post(
            '/sales/checkout',
            data=json.dumps(checkout_payload),
            content_type='application/json'
        )
        self.assertEqual(res_checkout.status_code, 200)
        data = res_checkout.get_json()
        self.assertTrue(data['success'])
        invoice_id = data['invoice_id']
        invoice_no = data['invoice_no']

        # 8. Verify product stock decreased
        db.session.refresh(prod)
        self.assertEqual(prod.quantity, initial_qty - sale_qty)

        # 9. Verify sale recorded in database and history
        sale = db.session.get(Sale, invoice_id)
        self.assertIsNotNone(sale)
        self.assertEqual(sale.invoice_no, invoice_no)
        self.assertEqual(sale.payment_method, 'upi')
        self.assertEqual(sale.customer_name, 'Aarav Mehta')
        self.assertEqual(len(sale.items), 1)
        self.assertEqual(sale.items[0].quantity, sale_qty)

        # 10. Generate and print invoice view
        res_inv = self.client.get(f'/sales/invoice/{invoice_id}')
        self.assertEqual(res_inv.status_code, 200)
        self.assertIn(invoice_no.encode(), res_inv.data)
        self.assertIn(b'Aarav Mehta', res_inv.data)
        self.assertIn(b'NET AMOUNT PAYABLE', res_inv.data)

    def test_workflow_11_dashboard_and_charts(self):
        """11. Check dashboard metrics and Chart.js endpoints"""
        self.client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'})
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Supermarket Dashboard', res.data)

        # Chart.js API JSON
        res_charts = self.client.get('/api/dashboard/charts')
        self.assertEqual(res_charts.status_code, 200)
        chart_data = res_charts.get_json()
        self.assertIn('seven_days', chart_data)
        self.assertIn('categories', chart_data)
        self.assertIn('top_products', chart_data)
        self.assertIn('stock_status', chart_data)
        self.assertIn('monthly_revenue', chart_data)

    def test_workflow_12_reports_and_csv_exports(self):
        """12. Generate reports and verify downloadable CSV outputs"""
        self.client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'})
        res_rep = self.client.get('/reports/')
        self.assertEqual(res_rep.status_code, 200)
        self.assertIn(b'Reports & Financial Analytics', res_rep.data)

        # CSV Exports
        res_csv_sales = self.client.get('/reports/export/sales')
        self.assertEqual(res_csv_sales.status_code, 200)
        self.assertIn("text/csv", res_csv_sales.headers["Content-Type"])
        self.assertIn(b'Invoice No,Date,Customer Name', res_csv_sales.data)

        res_csv_inv = self.client.get('/reports/export/inventory')
        self.assertEqual(res_csv_inv.status_code, 200)
        self.assertIn(b'Product ID,Name,SKU', res_csv_inv.data)

        res_csv_mov = self.client.get('/reports/export/movements')
        self.assertEqual(res_csv_mov.status_code, 200)
        self.assertIn(b'Movement ID,Timestamp,Product Name', res_csv_mov.data)

    def test_workflow_13_low_stock_alerts(self):
        """13. Test low stock identification"""
        low_items = Product.query.filter(
            Product.is_active == True,
            Product.quantity <= Product.min_stock_level
        ).all()
        self.assertGreater(len(low_items), 0)
        for item in low_items:
            self.assertTrue(item.is_low_stock or item.is_out_of_stock)

    def test_workflow_14_role_based_access(self):
        """14. Verify role-based access controls for admin vs staff"""
        # Log in as Staff
        self.client.post('/auth/login', data={'username': 'staff', 'password': 'staff123'})

        # Staff attempts to add product (should be denied and redirected)
        res = self.client.post('/products/add', data={
            'name': 'Unauthorized Product',
            'sku': 'UNAUTH-001'
        }, follow_redirects=True)
        self.assertIn(b'Access denied. Admin privileges required', res.data)

        # Staff can access POS and view products
        res_pos = self.client.get('/sales/')
        self.assertEqual(res_pos.status_code, 200)

if __name__ == '__main__':
    unittest.main()
