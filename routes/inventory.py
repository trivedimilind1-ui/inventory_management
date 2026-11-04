from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Product, Category, StockMovement, ActivityLog

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
@login_required
def index():
    tab = request.args.get('tab', 'stock')  # 'stock' or 'movements'
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()  # 'all', 'low_stock', 'out_of_stock'
    movement_type = request.args.get('movement_type', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 15

    # Products query
    prod_query = Product.query.filter(Product.is_active == True)
    if search:
        prod_query = prod_query.filter(
            (Product.name.ilike(f'%{search}%')) |
            (Product.sku.ilike(f'%{search}%')) |
            (Product.brand.ilike(f'%{search}%'))
        )
    if status_filter == 'low_stock':
        prod_query = prod_query.filter(Product.quantity <= Product.min_stock_level, Product.quantity > 0)
    elif status_filter == 'out_of_stock':
        prod_query = prod_query.filter(Product.quantity <= 0)

    stock_pagination = prod_query.order_by(Product.quantity.asc()).paginate(page=page, per_page=per_page, error_out=False)

    # Movements query
    mov_query = StockMovement.query
    if search:
        mov_query = mov_query.join(Product).filter(
            (Product.name.ilike(f'%{search}%')) |
            (Product.sku.ilike(f'%{search}%')) |
            (StockMovement.reason.ilike(f'%{search}%')) |
            (StockMovement.reference_id.ilike(f'%{search}%'))
        )
    if movement_type:
        mov_query = mov_query.filter(StockMovement.movement_type == movement_type)

    movement_pagination = mov_query.order_by(StockMovement.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    # Stock counts
    total_items = Product.query.filter_by(is_active=True).count()
    low_stock_count = Product.query.filter(Product.is_active == True, Product.quantity <= Product.min_stock_level, Product.quantity > 0).count()
    out_of_stock_count = Product.query.filter(Product.is_active == True, Product.quantity <= 0).count()

    all_active_products = Product.query.filter_by(is_active=True).order_by(Product.name.asc()).all()

    return render_template(
        'inventory.html',
        tab=tab,
        stock_pagination=stock_pagination,
        movement_pagination=movement_pagination,
        search=search,
        status_filter=status_filter,
        movement_type=movement_type,
        total_items=total_items,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        all_products=all_active_products
    )


@inventory_bp.route('/add-stock', methods=['POST'])
@login_required
def add_stock():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int)
    reason = request.form.get('reason', '').strip() or 'Supplier stock replenishment'
    reference_id = request.form.get('reference_id', '').strip() or 'STK-IN'

    if not product_id or not quantity or quantity <= 0:
        flash('Please select a product and enter a valid positive quantity.', 'danger')
        return redirect(url_for('inventory.index'))

    product = db.get_or_404(Product, product_id)

    try:
        prev_qty = product.quantity
        new_qty = prev_qty + quantity
        product.quantity = new_qty

        movement = StockMovement(
            product_id=product.id,
            movement_type='in',
            quantity=quantity,
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            reason=reason,
            reference_id=reference_id,
            user_id=current_user.id
        )
        db.session.add(movement)

        ActivityLog.log(
            'STOCK_IN', 'Stock',
            f'Added {quantity} {product.unit} to {product.name} (Qty: {prev_qty} -> {new_qty})',
            user_id=current_user.id,
            entity_id=product.id
        )

        db.session.commit()
        flash(f'Successfully added {quantity} {product.unit} to "{product.name}". New stock: {new_qty}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to add stock: {str(e)}', 'danger')

    return redirect(url_for('inventory.index'))


@inventory_bp.route('/adjust', methods=['POST'])
@login_required
def adjust_stock():
    product_id = request.form.get('product_id', type=int)
    adjustment_type = request.form.get('adjustment_type', 'reduction')  # 'reduction' or 'set'
    quantity = request.form.get('quantity', type=int)
    reason = request.form.get('reason', '').strip()
    notes = request.form.get('notes', '').strip()

    if not product_id or quantity is None:
        flash('Invalid product or quantity specified.', 'danger')
        return redirect(url_for('inventory.index'))

    product = db.get_or_404(Product, product_id)
    prev_qty = product.quantity

    if adjustment_type == 'reduction':
        if quantity <= 0:
            flash('Reduction quantity must be greater than zero.', 'danger')
            return redirect(url_for('inventory.index'))
        
        # Rule #1: Stock cannot become negative
        if prev_qty - quantity < 0:
            flash(f'Cannot reduce stock by {quantity}. Current available quantity is only {prev_qty}. Stock cannot be negative!', 'danger')
            return redirect(url_for('inventory.index'))

        new_qty = prev_qty - quantity
        qty_change = -quantity
        mov_type = 'out'
    else:  # Set absolute count
        if quantity < 0:
            flash('Stock count cannot be negative.', 'danger')
            return redirect(url_for('inventory.index'))
        new_qty = quantity
        qty_change = new_qty - prev_qty
        mov_type = 'adjustment'

    full_reason = f"{reason} - {notes}" if notes else reason

    try:
        product.quantity = new_qty

        movement = StockMovement(
            product_id=product.id,
            movement_type=mov_type,
            quantity=qty_change,
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            reason=full_reason or 'Stock audit adjustment',
            reference_id='ADJ-' + datetime.now().strftime('%Y%m%d%H%M'),
            user_id=current_user.id
        )
        db.session.add(movement)

        ActivityLog.log(
            'ADJUST', 'Stock',
            f'Adjusted {product.name} ({product.sku}): {prev_qty} -> {new_qty}. Reason: {full_reason}',
            user_id=current_user.id,
            entity_id=product.id
        )

        db.session.commit()
        flash(f'Stock for "{product.name}" updated successfully to {new_qty} {product.unit}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to adjust stock: {str(e)}', 'danger')

    return redirect(url_for('inventory.index'))
