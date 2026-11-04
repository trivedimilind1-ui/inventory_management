from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func
from models import db, Product, Category, Sale, SaleItem, StockMovement, ActivityLog

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    today = date.today()
    start_of_today = datetime.combine(today, datetime.min.time())

    # 1. KPI Statistics
    total_products = Product.query.filter_by(is_active=True).count()
    total_categories = Category.query.filter_by(is_active=True).count()
    
    # Stock aggregations
    stock_stats = db.session.query(
        func.coalesce(func.sum(Product.quantity), 0),
        func.coalesce(func.sum(Product.quantity * Product.purchase_price), 0.0)
    ).filter(Product.is_active == True).first()

    total_stock_quantity = int(stock_stats[0] if stock_stats else 0)
    total_inventory_value = float(stock_stats[1] if stock_stats else 0.0)

    # Low stock & Out of stock
    low_stock_products = Product.query.filter(
        Product.is_active == True,
        Product.quantity <= Product.min_stock_level,
        Product.quantity > 0
    ).all()

    out_of_stock_products = Product.query.filter(
        Product.is_active == True,
        Product.quantity <= 0
    ).all()

    # Sales & Revenue
    total_sales_count = Sale.query.filter_by(status='completed').count()
    
    today_revenue_res = db.session.query(
        func.coalesce(func.sum(Sale.total_amount), 0.0)
    ).filter(
        Sale.status == 'completed',
        Sale.created_at >= start_of_today
    ).scalar()
    today_revenue = float(today_revenue_res or 0.0)

    total_revenue_res = db.session.query(
        func.coalesce(func.sum(Sale.total_amount), 0.0)
    ).filter(Sale.status == 'completed').scalar()
    total_revenue = float(total_revenue_res or 0.0)

    # 2. Recent activities and alerts
    recent_sales = Sale.query.filter_by(status='completed').order_by(Sale.created_at.desc()).limit(6).all()
    recent_movements = StockMovement.query.order_by(StockMovement.created_at.desc()).limit(6).all()
    recent_products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(5).all()

    kpi = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_stock_quantity': total_stock_quantity,
        'total_inventory_value': total_inventory_value,
        'low_stock_count': len(low_stock_products),
        'out_of_stock_count': len(out_of_stock_products),
        'total_sales_count': total_sales_count,
        'today_revenue': today_revenue,
        'total_revenue': total_revenue
    }

    return render_template(
        'dashboard.html',
        kpi=kpi,
        low_stock_list=low_stock_products[:5],
        out_of_stock_list=out_of_stock_products[:5],
        recent_sales=recent_sales,
        recent_movements=recent_movements,
        recent_products=recent_products
    )


@dashboard_bp.route('/api/dashboard/charts')
@login_required
def charts_data():
    today = date.today()

    # 1. Last 7 Days Sales Trend (Daily revenue & orders)
    seven_days_labels = []
    seven_days_revenue = []
    seven_days_orders = []

    for i in range(6, -1, -1):
        day_date = today - timedelta(days=i)
        day_start = datetime.combine(day_date, datetime.min.time())
        day_end = datetime.combine(day_date, datetime.max.time())

        day_label = day_date.strftime('%a (%d %b)')
        seven_days_labels.append(day_label)

        day_sales = db.session.query(
            func.coalesce(func.sum(Sale.total_amount), 0.0),
            func.count(Sale.id)
        ).filter(
            Sale.status == 'completed',
            Sale.created_at >= day_start,
            Sale.created_at <= day_end
        ).first()

        seven_days_revenue.append(float(day_sales[0] or 0.0))
        seven_days_orders.append(int(day_sales[1] or 0))

    # 2. Products by Category (Category distribution)
    cat_distribution = db.session.query(
        Category.name,
        func.count(Product.id)
    ).join(Product, Product.category_id == Category.id)\
     .filter(Category.is_active == True, Product.is_active == True)\
     .group_by(Category.name)\
     .order_by(func.count(Product.id).desc())\
     .all()

    cat_labels = [row[0] for row in cat_distribution]
    cat_counts = [int(row[1]) for row in cat_distribution]

    # 3. Top 5 Selling Products
    top_selling = db.session.query(
        SaleItem.product_name,
        func.sum(SaleItem.quantity).label('units_sold'),
        func.sum(SaleItem.line_total).label('sales_value')
    ).join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.status == 'completed')\
     .group_by(SaleItem.product_name)\
     .order_by(func.sum(SaleItem.quantity).desc())\
     .limit(5)\
     .all()

    top_prod_labels = [row[0][:22] + '...' if len(row[0]) > 25 else row[0] for row in top_selling]
    top_prod_quantities = [int(row[1]) for row in top_selling]
    top_prod_values = [float(row[2]) for row in top_selling]

    # 4. Stock Availability Overview (In Stock, Low Stock, Out of Stock)
    in_stock_count = Product.query.filter(
        Product.is_active == True,
        Product.quantity > Product.min_stock_level
    ).count()

    low_stock_count = Product.query.filter(
        Product.is_active == True,
        Product.quantity <= Product.min_stock_level,
        Product.quantity > 0
    ).count()

    out_of_stock_count = Product.query.filter(
        Product.is_active == True,
        Product.quantity <= 0
    ).count()

    # 5. Monthly Revenue for current year (Jan to Dec)
    current_year = today.year
    months_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_revenue = [0.0] * 12

    for m in range(1, 13):
        m_start = datetime(current_year, m, 1)
        if m == 12:
            m_end = datetime(current_year + 1, 1, 1)
        else:
            m_end = datetime(current_year, m + 1, 1)

        m_rev = db.session.query(
            func.coalesce(func.sum(Sale.total_amount), 0.0)
        ).filter(
            Sale.status == 'completed',
            Sale.created_at >= m_start,
            Sale.created_at < m_end
        ).scalar()

        monthly_revenue[m - 1] = float(m_rev or 0.0)

    return jsonify({
        'seven_days': {
            'labels': seven_days_labels,
            'revenue': seven_days_revenue,
            'orders': seven_days_orders
        },
        'categories': {
            'labels': cat_labels,
            'counts': cat_counts
        },
        'top_products': {
            'labels': top_prod_labels,
            'quantities': top_prod_quantities,
            'values': top_prod_values
        },
        'stock_status': {
            'labels': ['In Stock', 'Low Stock', 'Out of Stock'],
            'counts': [in_stock_count, low_stock_count, out_of_stock_count]
        },
        'monthly_revenue': {
            'labels': months_labels,
            'revenue': monthly_revenue
        }
    })
