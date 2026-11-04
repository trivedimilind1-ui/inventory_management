from datetime import datetime, timezone
from . import db

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    movement_type = db.Column(db.String(30), nullable=False)  # 'in', 'out', 'adjustment', 'sale', 'return'
    quantity = db.Column(db.Integer, nullable=False)           # positive for addition, negative for reduction
    previous_quantity = db.Column(db.Integer, nullable=False)
    new_quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=True)          # e.g., 'Restock from supplier', 'Damaged goods', 'Sale INV-1002'
    reference_id = db.Column(db.String(100), nullable=True)    # Invoice No, PO Number, or audit code
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown Product',
            'sku': self.product.sku if self.product else '',
            'movement_type': self.movement_type,
            'quantity': self.quantity,
            'previous_quantity': self.previous_quantity,
            'new_quantity': self.new_quantity,
            'reason': self.reason or '',
            'reference_id': self.reference_id or '',
            'user_name': self.user.full_name if self.user else 'System',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }

    def __repr__(self):
        return f'<StockMovement Prod:{self.product_id} Type:{self.movement_type} Qty:{self.quantity}>'


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    po_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    order_date = db.Column(db.Date, nullable=False)
    expected_date = db.Column(db.Date, nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, received, cancelled
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    items = db.relationship('PurchaseOrderItem', backref='purchase_order', cascade='all, delete-orphan', lazy=True)
    creator = db.relationship('User', backref='purchase_orders', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'po_number': self.po_number,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.company_name if self.supplier else 'Unknown',
            'creator_name': self.creator.full_name if self.creator else 'System',
            'order_date': self.order_date.strftime('%Y-%m-%d') if self.order_date else '',
            'expected_date': self.expected_date.strftime('%Y-%m-%d') if self.expected_date else '',
            'total_amount': float(self.total_amount),
            'status': self.status,
            'notes': self.notes or '',
            'items_count': len(self.items)
        }


class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    line_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    received_quantity = db.Column(db.Integer, nullable=False, default=0)

    product = db.relationship('Product', lazy=True)
