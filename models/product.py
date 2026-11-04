from datetime import datetime, timezone
from . import db

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    sku = db.Column(db.String(64), unique=True, nullable=False, index=True)
    barcode = db.Column(db.String(64), nullable=True, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True, index=True)
    brand = db.Column(db.String(100), default='Generic', nullable=False)
    purchase_price = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    selling_price = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    min_stock_level = db.Column(db.Integer, nullable=False, default=10)
    unit = db.Column(db.String(20), default='pcs', nullable=False)  # pcs, kg, ltr, pack, box, bottle
    expiry_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    stock_movements = db.relationship('StockMovement', backref='product', lazy=True)
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level and self.quantity > 0

    @property
    def is_out_of_stock(self):
        return self.quantity <= 0

    @property
    def stock_status(self):
        if self.quantity <= 0:
            return 'out_of_stock'
        elif self.quantity <= self.min_stock_level:
            return 'low_stock'
        return 'in_stock'

    @property
    def margin(self):
        if self.selling_price and float(self.selling_price) > 0:
            sp = float(self.selling_price)
            pp = float(self.purchase_price)
            return round(((sp - pp) / sp) * 100, 1)
        return 0.0

    @property
    def total_value(self):
        return round(float(self.purchase_price) * self.quantity, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'barcode': self.barcode or self.sku,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'Uncategorized',
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.company_name if self.supplier else 'None',
            'brand': self.brand,
            'purchase_price': float(self.purchase_price),
            'selling_price': float(self.selling_price),
            'quantity': self.quantity,
            'min_stock_level': self.min_stock_level,
            'unit': self.unit,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d') if self.expiry_date else None,
            'description': self.description or '',
            'stock_status': self.stock_status,
            'is_low_stock': self.is_low_stock,
            'is_out_of_stock': self.is_out_of_stock,
            'margin': self.margin,
            'total_value': self.total_value,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }

    def __repr__(self):
        return f'<Product {self.name} [{self.sku}] (Qty: {self.quantity})>'
