from datetime import datetime, timezone
from . import db

class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_no = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    customer_name = db.Column(db.String(100), default='Walk-in Customer', nullable=False)
    customer_phone = db.Column(db.String(20), nullable=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=5.0)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    payment_method = db.Column(db.String(20), default='cash', nullable=False)  # cash, card, upi
    status = db.Column(db.String(20), default='completed', nullable=False)    # completed, cancelled
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    items = db.relationship('SaleItem', backref='sale', cascade='all, delete-orphan', lazy=True)

    @property
    def total_cost(self):
        return sum(float(item.unit_cost) * item.quantity for item in self.items)

    @property
    def gross_profit(self):
        return sum(float(item.line_profit) for item in self.items)

    @property
    def total_items_count(self):
        return sum(item.quantity for item in self.items)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_no': self.invoice_no,
            'user_id': self.user_id,
            'cashier_name': self.cashier.full_name if self.cashier else 'System',
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone or '',
            'subtotal': float(self.subtotal),
            'tax_rate': float(self.tax_rate),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'total_amount': float(self.total_amount),
            'payment_method': self.payment_method,
            'status': self.status,
            'items_count': self.total_items_count,
            'gross_profit': round(self.gross_profit, 2),
            'notes': self.notes or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }

    def __repr__(self):
        return f'<Sale {self.invoice_no} (₹{self.total_amount})>'


class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True, index=True)
    product_name = db.Column(db.String(150), nullable=False)
    sku = db.Column(db.String(64), nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    line_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    line_profit = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'sku': self.sku,
            'unit_cost': float(self.unit_cost),
            'unit_price': float(self.unit_price),
            'quantity': self.quantity,
            'line_total': float(self.line_total),
            'line_profit': float(self.line_profit)
        }

    def __repr__(self):
        return f'<SaleItem {self.product_name} x {self.quantity}>'
