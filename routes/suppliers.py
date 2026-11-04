from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Supplier, Product, ActivityLog
from routes import admin_required

suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

@suppliers_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    query = Supplier.query.filter(Supplier.is_active == True)

    if search:
        query = query.filter(
            (Supplier.name.ilike(f'%{search}%')) |
            (Supplier.company_name.ilike(f'%{search}%')) |
            (Supplier.phone.ilike(f'%{search}%')) |
            (Supplier.email.ilike(f'%{search}%')) |
            (Supplier.gst_number.ilike(f'%{search}%'))
        )

    suppliers = query.order_by(Supplier.company_name.asc()).all()
    return render_template('suppliers.html', suppliers=suppliers, search=search)


@suppliers_bp.route('/<int:supplier_id>')
@login_required
def detail(supplier_id):
    supplier = db.get_or_404(Supplier, supplier_id)
    products = Product.query.filter_by(supplier_id=supplier.id, is_active=True).all()
    return render_template('supplier_detail.html', supplier=supplier, products=products)


@suppliers_bp.route('/add', methods=['POST'])
@login_required
@admin_required
def add():
    name = request.form.get('name', '').strip()
    company_name = request.form.get('company_name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    gst_number = request.form.get('gst_number', '').strip()

    if not name or not company_name or not phone:
        flash('Contact Name, Company Name, and Phone are required.', 'danger')
        return redirect(url_for('suppliers.index'))

    try:
        sup = Supplier(
            name=name,
            company_name=company_name,
            phone=phone,
            email=email or None,
            address=address or None,
            gst_number=gst_number or None,
            is_active=True
        )
        db.session.add(sup)
        db.session.flush()

        ActivityLog.log('CREATE', 'Supplier', f'Added supplier: {company_name} ({name})', user_id=current_user.id, entity_id=sup.id)
        db.session.commit()
        flash(f'Supplier "{company_name}" added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding supplier: {str(e)}', 'danger')

    return redirect(url_for('suppliers.index'))


@suppliers_bp.route('/edit/<int:supplier_id>', methods=['POST'])
@login_required
@admin_required
def edit(supplier_id):
    sup = db.get_or_404(Supplier, supplier_id)
    name = request.form.get('name', '').strip()
    company_name = request.form.get('company_name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    gst_number = request.form.get('gst_number', '').strip()

    if not name or not company_name or not phone:
        flash('Contact Name, Company Name, and Phone are required.', 'danger')
        return redirect(url_for('suppliers.index'))

    try:
        sup.name = name
        sup.company_name = company_name
        sup.phone = phone
        sup.email = email or None
        sup.address = address or None
        sup.gst_number = gst_number or None

        ActivityLog.log('UPDATE', 'Supplier', f'Updated supplier: {company_name}', user_id=current_user.id, entity_id=sup.id)
        db.session.commit()
        flash(f'Supplier "{company_name}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating supplier: {str(e)}', 'danger')

    return redirect(url_for('suppliers.index'))


@suppliers_bp.route('/delete/<int:supplier_id>', methods=['POST'])
@login_required
@admin_required
def delete(supplier_id):
    sup = db.get_or_404(Supplier, supplier_id)
    company = sup.company_name

    try:
        sup.is_active = False
        # Reassign products supplier to NULL or keep association intact for history
        Product.query.filter_by(supplier_id=sup.id).update({'supplier_id': None})
        ActivityLog.log('DELETE', 'Supplier', f'Removed supplier: {company}', user_id=current_user.id, entity_id=sup.id)
        db.session.commit()
        flash(f'Supplier "{company}" has been removed.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting supplier: {str(e)}', 'danger')

    return redirect(url_for('suppliers.index'))


@suppliers_bp.route('/api/<int:supplier_id>')
@login_required
def get_supplier_json(supplier_id):
    sup = db.get_or_404(Supplier, supplier_id)
    return jsonify(sup.to_dict())
