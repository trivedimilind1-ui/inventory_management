from datetime import datetime, timezone
from . import db

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False)        # 'CREATE', 'UPDATE', 'DELETE', 'SALE', 'STOCK_IN', 'ADJUST'
    entity_type = db.Column(db.String(50), nullable=False)   # 'Product', 'Category', 'Sale', 'Supplier', 'Stock'
    entity_id = db.Column(db.String(50), nullable=True)
    details = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    @staticmethod
    def log(action, entity_type, details, user_id=None, entity_id=None, ip_address=None):
        try:
            entry = ActivityLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                details=details,
                ip_address=ip_address
            )
            db.session.add(entry)
        except Exception:
            pass  # Non-blocking log helper

    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user.full_name if self.user else 'System',
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': self.details,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }

    def __repr__(self):
        return f'<ActivityLog {self.action} on {self.entity_type}: {self.details}>'
