from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash("Access denied. Admin privileges required for this action.", "danger")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function
