from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .category import Category
from .supplier import Supplier
from .product import Product
from .sale import Sale, SaleItem
from .inventory import StockMovement, PurchaseOrder, PurchaseOrderItem
from .activity import ActivityLog

__all__ = [
    'db',
    'User',
    'Category',
    'Supplier',
    'Product',
    'Sale',
    'SaleItem',
    'StockMovement',
    'PurchaseOrder',
    'PurchaseOrderItem',
    'ActivityLog'
]
