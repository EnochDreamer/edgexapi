"""WSGI entrypoint for running the Flask app with WSGI servers like gunicorn.

This module exposes a module-level ``app`` object so you can run:

    gunicorn --bind 0.0.0.0:8000 wsgi:app

Note: gunicorn is not supported natively on Windows. Use WSL, Docker, or a
Windows-compatible WSGI server (e.g. waitress) when running on Windows.
"""
from flaskr import create_app
import os

from flaskr.extensions import db


# Create the Flask application instance using the factory.
app = create_app()

# Optional: initialize database on startup when explicitly requested.
# Set INIT_DB_ON_START=1 (or true/yes) in the environment to enable.
if os.getenv("INIT_DB_ON_START", "").lower() in ("1", "true", "yes"):
    # Run inside application context so SQLAlchemy has app config
    with app.app_context():
        db.create_all()
        print("Database initialized via INIT_DB_ON_START")


