import json
import random
from datetime import datetime, timezone
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Product, Sale, SaleItem, StockMovement, ActivityLog

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/')
@login_required
def index():
    # Billing POS Terminal
    products = Product.query.filter(Product.is_active == True, Product.quantity > 0).order_by(Product.name.asc()).all()
    default_tax = current_app.config.get('DEFAULT_TAX_RATE', 5.0)
    return render_template('sales.html', products=products, default_tax=default_tax)


@sales_bp.route('/history')
@login_required
def history():
    search = request.args.get('search', '').strip()
    payment_method = request.args.get('payment_method', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 15

    query = Sale.query

    if search:
        query = query.filter(
            (Sale.invoice_no.ilike(f'%{search}%')) |
            (Sale.customer_name.ilike(f'%{search}%')) |
            (Sale.customer_phone.ilike(f'%{search}%'))
        )

    if payment_method:
        query = query.filter(Sale.payment_method == payment_method)

    pagination = query.order_by(Sale.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    sales = pagination.items

    return render_template('sales_history.html', sales=sales, pagination=pagination, search=search, payment_method=payment_method)


@sales_bp.route('/api/search-products')
@login_required
def search_products():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    products = Product.query.filter(
        Product.is_active == True,
        (Product.name.ilike(f'%{q}%')) |
        (Product.sku.ilike(f'%{q}%')) |
        (Product.barcode.ilike(f'%{q}%')) |
        (Product.brand.ilike(f'%{q}%'))
    ).limit(10).all()

    return jsonify([p.to_dict() for p in products])


@sales_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    try:
        data = request.get_json(silent=True) or request.form

        # Extract items
        items_raw = data.get('items')
        if isinstance(items_raw, str):
            try:
                items_data = json.loads(items_raw)
            except Exception:
                items_data = []
        else:
            items_data = items_raw or []

        if not items_data or len(items_data) == 0:
            return jsonify({'success': False, 'message': 'Cart is empty. Please add items before checkout.'}), 400

        customer_name = (data.get('customer_name') or 'Walk-in Customer').strip()
        customer_phone = (data.get('customer_phone') or '').strip()
        payment_method = data.get('payment_method', 'cash').strip().lower()
        discount_amount = Decimal(str(max(0.0, float(data.get('discount_amount') or 0.0))))
        tax_rate = Decimal(str(max(0.0, float(data.get('tax_rate') or current_app.config.get('DEFAULT_TAX_RATE', 5.0)))))
        notes = (data.get('notes') or '').strip()

        if payment_method not in ['cash', 'card', 'upi']:
            payment_method = 'cash'

        # Generate unique Invoice Number
        date_str = datetime.now().strftime('%Y%m%d')
        random_suffix = random.randint(1000, 9999)
        invoice_no = f"INV-{date_str}-{random_suffix}"

        # Ensure uniqueness
        while Sale.query.filter_by(invoice_no=invoice_no).first():
            random_suffix = random.randint(1000, 9999)
            invoice_no = f"INV-{date_str}-{random_suffix}"

        subtotal = Decimal('0.00')
        sale_items_to_save = []
        stock_updates = []

        # Validate stock availability and calculate totals atomically
        for item in items_data:
            p_id = int(item['product_id'])
            qty = int(item['quantity'])

            if qty <= 0:
                return jsonify({'success': False, 'message': 'Invalid item quantity.'}), 400

            product = Product.query.filter_by(id=p_id, is_active=True).with_for_update().first()
            if not product:
                return jsonify({'success': False, 'message': f'Product ID {p_id} not found.'}), 404

            # Rule #1 & #2: Check sufficient stock & prevent negative stock
            if product.quantity < qty:
                return jsonify({
                    'success': False,
                    'message': f'Insufficient stock for "{product.name}". Requested: {qty}, Available: {product.quantity}.'
                }), 400

            unit_price = Decimal(str(product.selling_price))
            unit_cost = Decimal(str(product.purchase_price))
            line_total = unit_price * qty
            line_profit = (unit_price - unit_cost) * qty

            subtotal += line_total

            sale_items_to_save.append({
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'unit_cost': unit_cost,
                'unit_price': unit_price,
                'quantity': qty,
                'line_total': line_total,
                'line_profit': line_profit,
                'product_ref': product
            })

        # Calculate taxes and total
        tax_amount = round(subtotal * (tax_rate / Decimal('100.00')), 2)
        total_amount = max(Decimal('0.00'), subtotal + tax_amount - discount_amount)

        # Create Sale
        sale = Sale(
            invoice_no=invoice_no,
            user_id=current_user.id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            payment_method=payment_method,
            status='completed',
            notes=notes
        )
        db.session.add(sale)
        db.session.flush()

        # Save Sale Items and Update Stock atomically
        for item_data in sale_items_to_save:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item_data['product_id'],
                product_name=item_data['product_name'],
                sku=item_data['sku'],
                unit_cost=item_data['unit_cost'],
                unit_price=item_data['unit_price'],
                quantity=item_data['quantity'],
                line_total=item_data['line_total'],
                line_profit=item_data['line_profit']
            )
            db.session.add(sale_item)

            # Reduce product stock
            prod = item_data['product_ref']
            prev_qty = prod.quantity
            new_qty = prev_qty - item_data['quantity']
            prod.quantity = new_qty

            # Log stock movement
            movement = StockMovement(
                product_id=prod.id,
                movement_type='sale',
                quantity=-item_data['quantity'],
                previous_quantity=prev_qty,
                new_quantity=new_qty,
                reason=f'Sale Invoice {invoice_no}',
                reference_id=invoice_no,
                user_id=current_user.id
            )
            db.session.add(movement)

        # Log Activity
        ActivityLog.log(
            'SALE', 'Sale',
            f'Completed sale {invoice_no} (Total: ₹{total_amount:.2f}, Items: {len(sale_items_to_save)})',
            user_id=current_user.id,
            entity_id=sale.id
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Sale completed successfully!',
            'invoice_id': sale.id,
            'invoice_no': sale.invoice_no,
            'total_amount': float(sale.total_amount),
            'redirect_url': url_for('sales.invoice', sale_id=sale.id)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Transaction error: {str(e)}'}), 500


@sales_bp.route('/invoice/<int:sale_id>')
@login_required
def invoice(sale_id):
    sale = db.get_or_404(Sale, sale_id)
    return render_template('invoice.html', sale=sale)
