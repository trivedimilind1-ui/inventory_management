from datetime import datetime, timezone
from . import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), default='bi-tag', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    products = db.relationship('Product', backref='category', lazy=True)

    @property
    def product_count(self):
        return sum(1 for p in self.products if p.is_active)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'icon': self.icon,
            'product_count': self.product_count,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }

    def __repr__(self):
        return f'<Category {self.name}>'
