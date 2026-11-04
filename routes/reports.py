import io
import csv
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from flask import Blueprint, render_template, request, make_response, jsonify
from flask_login import login_required
from sqlalchemy import func
from models import db, Product, Category, Sale, SaleItem, StockMovement, Supplier

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    # Filter dates
    period = request.args.get('period', 'month')  # 'today', 'week', 'month', 'year', 'custom'
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')

    today = date.today()

    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=6)
        end_date = today
    elif period == 'year':
        start_date = date(today.year, 1, 1)
        end_date = today
    elif period == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today - timedelta(days=29)
            end_date = today
    else:  # Default last 30 days / month
        period = 'month'
        start_date = today - timedelta(days=29)
        end_date = today

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    # 1. Sales & Revenue in Period
    sales_in_period = Sale.query.filter(
        Sale.status == 'completed',
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime
    ).all()

    total_orders = len(sales_in_period)
    total_revenue = sum(float(s.total_amount) for s in sales_in_period)
    total_tax = sum(float(s.tax_amount) for s in sales_in_period)
    total_discount = sum(float(s.discount_amount) for s in sales_in_period)

    # Gross Profit in Period (from SaleItem unit_cost)
    profit_res = db.session.query(
        func.coalesce(func.sum(SaleItem.line_profit), 0.0),
        func.coalesce(func.sum(SaleItem.quantity), 0)
    ).join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(
         Sale.status == 'completed',
         Sale.created_at >= start_datetime,
         Sale.created_at <= end_datetime
     ).first()

    gross_profit = float(profit_res[0] or 0.0)
    units_sold = int(profit_res[1] or 0)
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    profit_margin = round((gross_profit / total_revenue) * 100, 1) if total_revenue > 0 else 0.0

    # 2. Overall Inventory Valuation
    inv_valuation_res = db.session.query(
        func.coalesce(func.sum(Product.quantity * Product.purchase_price), 0.0),
        func.coalesce(func.sum(Product.quantity * Product.selling_price), 0.0),
        func.coalesce(func.sum(Product.quantity), 0)
    ).filter(Product.is_active == True).first()

    inventory_cost = float(inv_valuation_res[0] or 0.0)
    inventory_retail = float(inv_valuation_res[1] or 0.0)
    total_stock_units = int(inv_valuation_res[2] or 0)
    potential_profit = max(0.0, inventory_retail - inventory_cost)

    # 3. Best Selling Products in period
    best_sellers = db.session.query(
        SaleItem.product_name,
        SaleItem.sku,
        func.sum(SaleItem.quantity).label('qty_sold'),
        func.sum(SaleItem.line_total).label('revenue'),
        func.sum(SaleItem.line_profit).label('profit')
    ).join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(
         Sale.status == 'completed',
         Sale.created_at >= start_datetime,
         Sale.created_at <= end_datetime
     )\
     .group_by(SaleItem.product_name, SaleItem.sku)\
     .order_by(func.sum(SaleItem.quantity).desc())\
     .limit(5)\
     .all()

    # 4. Least Selling / Slow Moving Products
    # Products with active status and low/zero sales
    least_sellers = db.session.query(
        Product.name,
        Product.sku,
        Product.quantity,
        Product.selling_price,
        func.coalesce(func.sum(SaleItem.quantity), 0).label('qty_sold')
    ).outerjoin(SaleItem, Product.id == SaleItem.product_id)\
     .filter(Product.is_active == True)\
     .group_by(Product.id, Product.name, Product.sku, Product.quantity, Product.selling_price)\
     .order_by(func.coalesce(func.sum(SaleItem.quantity), 0).asc(), Product.quantity.desc())\
     .limit(5)\
     .all()

    # 5. Low-stock report table
    low_stock_items = Product.query.filter(
        Product.is_active == True,
        Product.quantity <= Product.min_stock_level
    ).order_by(Product.quantity.asc()).all()

    report_summary = {
        'period': period,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'total_orders': total_orders,
        'total_revenue': round(total_revenue, 2),
        'gross_profit': round(gross_profit, 2),
        'profit_margin': profit_margin,
        'units_sold': units_sold,
        'avg_order_value': avg_order_value,
        'total_tax': round(total_tax, 2),
        'total_discount': round(total_discount, 2),
        'inventory_cost': round(inventory_cost, 2),
        'inventory_retail': round(inventory_retail, 2),
        'total_stock_units': total_stock_units,
        'potential_profit': round(potential_profit, 2)
    }

    return render_template(
        'reports.html',
        summary=report_summary,
        best_sellers=best_sellers,
        least_sellers=least_sellers,
        low_stock_items=low_stock_items
    )


@reports_bp.route('/api/chart-data')
@login_required
def chart_data():
    period = request.args.get('period', 'month')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    today = date.today()

    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=6)
        end_date = today
    elif period == 'year':
        start_date = date(today.year, 1, 1)
        end_date = today
    elif period == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today - timedelta(days=29)
            end_date = today
    else:
        start_date = today - timedelta(days=29)
        end_date = today

    # Category Revenue Distribution
    cat_sales = db.session.query(
        Category.name,
        func.coalesce(func.sum(SaleItem.line_total), 0.0)
    ).join(Product, Product.category_id == Category.id)\
     .join(SaleItem, SaleItem.product_id == Product.id)\
     .join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(
         Sale.status == 'completed',
         Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
         Sale.created_at <= datetime.combine(end_date, datetime.max.time())
     )\
     .group_by(Category.name)\
     .order_by(func.sum(SaleItem.line_total).desc())\
     .all()

    # Daily trend within period (max 30 points)
    delta_days = (end_date - start_date).days + 1
    step = 1 if delta_days <= 30 else max(1, delta_days // 30)

    dates_labels = []
    daily_revenue = []
    daily_profit = []

    curr = start_date
    while curr <= end_date:
        next_curr = min(curr + timedelta(days=step - 1), end_date)
        d_start = datetime.combine(curr, datetime.min.time())
        d_end = datetime.combine(next_curr, datetime.max.time())

        day_label = curr.strftime('%d %b') if delta_days > 7 else curr.strftime('%a %d')
        dates_labels.append(day_label)

        day_data = db.session.query(
            func.coalesce(func.sum(Sale.total_amount), 0.0)
        ).filter(
            Sale.status == 'completed',
            Sale.created_at >= d_start,
            Sale.created_at <= d_end
        ).scalar()

        day_profit = db.session.query(
            func.coalesce(func.sum(SaleItem.line_profit), 0.0)
        ).join(Sale, Sale.id == SaleItem.sale_id)\
         .filter(
             Sale.status == 'completed',
             Sale.created_at >= d_start,
             Sale.created_at <= d_end
         ).scalar()

        daily_revenue.append(float(day_data or 0.0))
        daily_profit.append(float(day_profit or 0.0))
        curr = next_curr + timedelta(days=1)

    return jsonify({
        'trend': {
            'labels': dates_labels,
            'revenue': daily_revenue,
            'profit': daily_profit
        },
        'categories': {
            'labels': [row[0] for row in cat_sales],
            'revenue': [float(row[1]) for row in cat_sales]
        }
    })


@reports_bp.route('/export/sales')
@login_required
def export_sales_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Invoice No', 'Date', 'Customer Name', 'Customer Phone', 'Payment Method', 'Subtotal', 'Tax', 'Discount', 'Total Amount', 'Cashier', 'Status'])

    sales = Sale.query.order_by(Sale.created_at.desc()).all()
    for s in sales:
        writer.writerow([
            s.invoice_no,
            s.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            s.customer_name,
            s.customer_phone or 'N/A',
            s.payment_method.upper(),
            f"{s.subtotal:.2f}",
            f"{s.tax_amount:.2f}",
            f"{s.discount_amount:.2f}",
            f"{s.total_amount:.2f}",
            s.cashier.full_name if s.cashier else 'System',
            s.status
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=smartstock_sales_report.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@reports_bp.route('/export/inventory')
@login_required
def export_inventory_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Product ID', 'Name', 'SKU', 'Barcode', 'Category', 'Brand', 'Purchase Price', 'Selling Price', 'Quantity', 'Unit', 'Min Stock', 'Stock Status', 'Total Inventory Value (₹)'])

    products = Product.query.filter_by(is_active=True).order_by(Product.name.asc()).all()
    for p in products:
        writer.writerow([
            p.id,
            p.name,
            p.sku,
            p.barcode or p.sku,
            p.category.name if p.category else 'N/A',
            p.brand,
            f"{p.purchase_price:.2f}",
            f"{p.selling_price:.2f}",
            p.quantity,
            p.unit,
            p.min_stock_level,
            p.stock_status.replace('_', ' ').title(),
            f"{p.total_value:.2f}"
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=smartstock_inventory_valuation.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@reports_bp.route('/export/movements')
@login_required
def export_movements_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Movement ID', 'Timestamp', 'Product Name', 'SKU', 'Movement Type', 'Quantity Changed', 'Previous Qty', 'New Qty', 'Reason', 'Reference ID', 'Logged By'])

    movements = StockMovement.query.order_by(StockMovement.created_at.desc()).all()
    for m in movements:
        writer.writerow([
            m.id,
            m.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            m.product.name if m.product else 'N/A',
            m.product.sku if m.product else 'N/A',
            m.movement_type.upper(),
            m.quantity,
            m.previous_quantity,
            m.new_quantity,
            m.reason or '',
            m.reference_id or '',
            m.user.full_name if m.user else 'System'
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=smartstock_stock_movements.csv"
    response.headers["Content-type"] = "text/csv"
    return response
