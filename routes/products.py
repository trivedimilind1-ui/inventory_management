from datetime import datetime, timezone
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Product, Category, Supplier, StockMovement, ActivityLog
from routes import admin_required

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('/')
@login_required
def index():
    # Filtering and sorting parameters
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category', type=int)
    supplier_id = request.args.get('supplier', type=int)
    status = request.args.get('status', '').strip() # 'low_stock', 'out_of_stock'
    sort_by = request.args.get('sort', 'created_at_desc')
    page = request.args.get('page', 1, type=int)
    per_page = 15

    query = Product.query.filter(Product.is_active == True)

    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) |
            (Product.sku.ilike(f'%{search}%')) |
            (Product.brand.ilike(f'%{search}%')) |
            (Product.barcode.ilike(f'%{search}%'))
        )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if supplier_id:
        query = query.filter(Product.supplier_id == supplier_id)

    if status == 'low_stock':
        query = query.filter(Product.quantity <= Product.min_stock_level, Product.quantity > 0)
    elif status == 'out_of_stock':
        query = query.filter(Product.quantity <= 0)

    # Sorting
    if sort_by == 'price_asc':
        query = query.order_by(Product.selling_price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.selling_price.desc())
    elif sort_by == 'qty_asc':
        query = query.order_by(Product.quantity.asc())
    elif sort_by == 'qty_desc':
        query = query.order_by(Product.quantity.desc())
    elif sort_by == 'name_asc':
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    categories = Category.query.filter_by(is_active=True).order_by(Category.name.asc()).all()
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.company_name.asc()).all()

    return render_template(
        'products.html',
        products=products,
        pagination=pagination,
        categories=categories,
        suppliers=suppliers,
        search=search,
        selected_category=category_id,
        selected_supplier=supplier_id,
        selected_status=status,
        sort_by=sort_by
    )


@products_bp.route('/add', methods=['POST'])
@login_required
@admin_required
def add():
    name = request.form.get('name', '').strip()
    sku = request.form.get('sku', '').strip().upper()
    barcode = request.form.get('barcode', '').strip() or sku
    category_id = request.form.get('category_id', type=int)
    supplier_id = request.form.get('supplier_id', type=int)
    brand = request.form.get('brand', 'Generic').strip()
    purchase_price = request.form.get('purchase_price', type=float)
    selling_price = request.form.get('selling_price', type=float)
    quantity = request.form.get('quantity', 0, type=int)
    min_stock_level = request.form.get('min_stock_level', 10, type=int)
    unit = request.form.get('unit', 'pcs').strip()
    expiry_date_str = request.form.get('expiry_date', '').strip()
    description = request.form.get('description', '').strip()

    # Validations
    if not name or not sku or not category_id:
        flash('Product Name, SKU, and Category are mandatory fields.', 'danger')
        return redirect(url_for('products.index'))

    if purchase_price is None or purchase_price < 0 or selling_price is None or selling_price < 0:
        flash('Purchase and Selling prices must be positive numbers.', 'danger')
        return redirect(url_for('products.index'))

    if quantity < 0:
        flash('Initial stock quantity cannot be negative.', 'danger')
        return redirect(url_for('products.index'))

    # Check unique SKU
    existing_sku = Product.query.filter_by(sku=sku).first()
    if existing_sku:
        flash(f'A product with SKU "{sku}" already exists.', 'danger')
        return redirect(url_for('products.index'))

    expiry_date = None
    if expiry_date_str:
        try:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    try:
        new_product = Product(
            name=name,
            sku=sku,
            barcode=barcode,
            category_id=category_id,
            supplier_id=supplier_id if supplier_id else None,
            brand=brand,
            purchase_price=Decimal(str(purchase_price)),
            selling_price=Decimal(str(selling_price)),
            quantity=quantity,
            min_stock_level=min_stock_level,
            unit=unit,
            expiry_date=expiry_date,
            description=description,
            is_active=True
        )
        db.session.add(new_product)
        db.session.flush()

        # Log initial movement
        if quantity > 0:
            movement = StockMovement(
                product_id=new_product.id,
                movement_type='in',
                quantity=quantity,
                previous_quantity=0,
                new_quantity=quantity,
                reason='Initial stock on product creation',
                reference_id='PROD-INIT',
                user_id=current_user.id
            )
            db.session.add(movement)

        ActivityLog.log(
            'CREATE', 'Product',
            f'Added product: {name} (SKU: {sku}, Qty: {quantity})',
            user_id=current_user.id,
            entity_id=new_product.id
        )

        db.session.commit()
        flash(f'Product "{name}" added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding product: {str(e)}', 'danger')

    return redirect(url_for('products.index'))


@products_bp.route('/edit/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def edit(product_id):
    product = db.get_or_404(Product, product_id)

    name = request.form.get('name', '').strip()
    sku = request.form.get('sku', '').strip().upper()
    barcode = request.form.get('barcode', '').strip() or sku
    category_id = request.form.get('category_id', type=int)
    supplier_id = request.form.get('supplier_id', type=int)
    brand = request.form.get('brand', 'Generic').strip()
    purchase_price = request.form.get('purchase_price', type=float)
    selling_price = request.form.get('selling_price', type=float)
    min_stock_level = request.form.get('min_stock_level', 10, type=int)
    unit = request.form.get('unit', 'pcs').strip()
    expiry_date_str = request.form.get('expiry_date', '').strip()
    description = request.form.get('description', '').strip()

    if not name or not sku or not category_id:
        flash('Product Name, SKU, and Category are mandatory fields.', 'danger')
        return redirect(url_for('products.index'))

    # Check SKU uniqueness against other products
    other_prod = Product.query.filter(Product.sku == sku, Product.id != product.id).first()
    if other_prod:
        flash(f'SKU "{sku}" is already in use by another product.', 'danger')
        return redirect(url_for('products.index'))

    expiry_date = None
    if expiry_date_str:
        try:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    try:
        product.name = name
        product.sku = sku
        product.barcode = barcode
        product.category_id = category_id
        product.supplier_id = supplier_id if supplier_id else None
        product.brand = brand
        product.purchase_price = Decimal(str(purchase_price))
        product.selling_price = Decimal(str(selling_price))
        product.min_stock_level = min_stock_level
        product.unit = unit
        product.expiry_date = expiry_date
        product.description = description

        ActivityLog.log(
            'UPDATE', 'Product',
            f'Updated product: {name} (SKU: {sku})',
            user_id=current_user.id,
            entity_id=product.id
        )

        db.session.commit()
        flash(f'Product "{name}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating product: {str(e)}', 'danger')

    return redirect(url_for('products.index'))


@products_bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete(product_id):
    product = db.get_or_404(Product, product_id)
    prod_name = product.name
    sku = product.sku

    try:
        # Soft-delete to preserve sales and stock movement integrity (Rule #5)
        product.is_active = False

        ActivityLog.log(
            'DELETE', 'Product',
            f'Soft-deleted product: {prod_name} (SKU: {sku})',
            user_id=current_user.id,
            entity_id=product.id
        )

        db.session.commit()
        flash(f'Product "{prod_name}" has been removed successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'danger')

    return redirect(url_for('products.index'))


@products_bp.route('/api/<int:product_id>')
@login_required
def get_product_json(product_id):
    product = db.get_or_404(Product, product_id)
    return jsonify(product.to_dict())
