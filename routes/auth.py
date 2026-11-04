from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, ActivityLog

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not identifier or not password:
            flash('Please enter both username/email and password.', 'danger')
            return render_template('login.html', identifier=identifier)

        # Allow login by username OR email
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('This account is deactivated. Please contact store management.', 'danger')
                return render_template('login.html', identifier=identifier)

            login_user(user, remember=remember)
            ActivityLog.log('LOGIN', 'User', f'User {user.username} logged in', user_id=user.id)
            db.session.commit()

            next_page = request.args.get('next')
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'staff').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        if not username or not email or not full_name or not password:
            flash('All required fields must be filled.', 'danger')
            return render_template('register.html', **request.form)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html', **request.form)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', **request.form)

        if role not in ['admin', 'staff']:
            role = 'staff'

        if User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another.', 'danger')
            return render_template('register.html', **request.form)

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('register.html', **request.form)

        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            role=role,
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        ActivityLog.log('REGISTER', 'User', f'New user registered: {username} ({role})', user_id=new_user.id)
        db.session.commit()

        flash(f'Account created successfully! You can now log in as {role.capitalize()}.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    ActivityLog.log('LOGOUT', 'User', f'User {current_user.username} logged out', user_id=current_user.id)
    db.session.commit()
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
