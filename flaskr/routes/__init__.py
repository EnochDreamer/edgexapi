from .main import bp as main_bp
from .auth import bp as auth_bp
from .products import bp as products_bp
from .payments import bp as payments_bp
from .user import bp as user_bp


def register_blueprints(app):
    """Register all blueprint modules on the provided Flask app."""
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(payments_bp, url_prefix="/payments")
    app.register_blueprint(user_bp, url_prefix="/users")


