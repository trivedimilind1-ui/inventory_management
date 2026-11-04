import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config
from models import db, User, Product

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.products import products_bp
    from routes.categories import categories_bp
    from routes.inventory import inventory_bp
    from routes.sales import sales_bp
    from routes.suppliers import suppliers_bp
    from routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(reports_bp)

    # Context processor for templates
    @app.context_processor
    def inject_global_vars():
        low_stock_badge = 0
        try:
            low_stock_badge = Product.query.filter(
                Product.is_active == True,
                Product.quantity <= Product.min_stock_level
            ).count()
        except Exception:
            pass

        return {
            'store_name': app.config.get('STORE_NAME', 'SmartStock Supermarket'),
            'store_tagline': app.config.get('STORE_TAGLINE', ''),
            'store_address': app.config.get('STORE_ADDRESS', ''),
            'store_phone': app.config.get('STORE_PHONE', ''),
            'store_email': app.config.get('STORE_EMAIL', ''),
            'store_gstin': app.config.get('STORE_GSTIN', ''),
            'store_currency': app.config.get('STORE_CURRENCY', '₹'),
            'low_stock_badge_count': low_stock_badge
        }

    # Auto-initialize and seed DB
    with app.app_context():
        try:
            db.create_all()
            from database.seed import seed_database
            seed_database(app)
        except Exception as e:
            app.logger.warning(f"Database initialization note: {e}")

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template_error(404, "Page Not Found", "The requested page does not exist.")

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template_error(500, "Internal Server Error", "Something went wrong on the server.")

    def render_template_error(code, title, message):
        from flask import render_template
        return render_template('base.html', error_code=code, error_title=title, error_message=message), code

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    print(f"Starting SmartStock Supermarket on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
