from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Category, Product, ActivityLog
from routes import admin_required

categories_bp = Blueprint('categories', __name__, url_prefix='/categories')

@categories_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    query = Category.query.filter(Category.is_active == True)

    if search:
        query = query.filter(Category.name.ilike(f'%{search}%') | Category.description.ilike(f'%{search}%'))

    categories = query.order_by(Category.name.asc()).all()
    return render_template('categories.html', categories=categories, search=search)


@categories_bp.route('/add', methods=['POST'])
@login_required
@admin_required
def add():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', 'bi-tag').strip()

    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('categories.index'))

    existing = Category.query.filter(Category.name.ilike(name)).first()
    if existing:
        flash(f'A category named "{name}" already exists.', 'danger')
        return redirect(url_for('categories.index'))

    try:
        cat = Category(name=name, description=description, icon=icon, is_active=True)
        db.session.add(cat)
        db.session.flush()

        ActivityLog.log('CREATE', 'Category', f'Created category: {name}', user_id=current_user.id, entity_id=cat.id)
        db.session.commit()
        flash(f'Category "{name}" created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating category: {str(e)}', 'danger')

    return redirect(url_for('categories.index'))


@categories_bp.route('/edit/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def edit(category_id):
    cat = db.get_or_404(Category, category_id)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', cat.icon).strip()

    if not name:
        flash('Category name cannot be empty.', 'danger')
        return redirect(url_for('categories.index'))

    existing = Category.query.filter(Category.name.ilike(name), Category.id != cat.id).first()
    if existing:
        flash(f'Another category named "{name}" already exists.', 'danger')
        return redirect(url_for('categories.index'))

    try:
        cat.name = name
        cat.description = description
        cat.icon = icon
        ActivityLog.log('UPDATE', 'Category', f'Updated category: {name}', user_id=current_user.id, entity_id=cat.id)
        db.session.commit()
        flash(f'Category "{name}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating category: {str(e)}', 'danger')

    return redirect(url_for('categories.index'))


@categories_bp.route('/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete(category_id):
    cat = db.get_or_404(Category, category_id)
    
    # Requirement: Prevent deleting categories that still contain products
    active_products_count = Product.query.filter_by(category_id=cat.id, is_active=True).count()
    if active_products_count > 0:
        flash(f'Cannot delete category "{cat.name}" because it still contains {active_products_count} active product(s). Please reassign or delete these products first.', 'danger')
        return redirect(url_for('categories.index'))

    try:
        cat_name = cat.name
        cat.is_active = False
        ActivityLog.log('DELETE', 'Category', f'Deleted category: {cat_name}', user_id=current_user.id, entity_id=cat.id)
        db.session.commit()
        flash(f'Category "{cat_name}" was successfully deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'danger')

    return redirect(url_for('categories.index'))
