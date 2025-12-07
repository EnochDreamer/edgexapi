import os
from dotenv import load_dotenv
from flask import Flask

from .extensions import db
from .routes import register_blueprints

load_dotenv()
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

required_vars = {
    'DB_NAME': DB_NAME,
    'DB_USER': DB_USER,
    'DB_PASSWORD': DB_PASSWORD,
}
missing_vars = [key for key, value in required_vars.items() if not value]
if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}. "
        "Please set them in your .env file."
    )




def create_app():
    app = Flask(__name__)
    DB_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'

    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    db.init_app(app)

    from . import models  # noqa: F401 - ensure models are registered

    register_blueprints(app)

    @app.cli.command("init-db")
    def init_db_command():
        """Create database tables."""
        db.create_all()
        print("Database initialized.")

    return app