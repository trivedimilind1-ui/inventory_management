from datetime import datetime, timezone
from . import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    company_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    gst_number = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    products = db.relationship('Product', backref='supplier', lazy=True)
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy=True)

    @property
    def product_count(self):
        return sum(1 for p in self.products if p.is_active)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'company_name': self.company_name,
            'phone': self.phone,
            'email': self.email or '',
            'address': self.address or '',
            'gst_number': self.gst_number or '',
            'product_count': self.product_count,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }

    def __repr__(self):
        return f'<Supplier {self.company_name} ({self.name})>'
