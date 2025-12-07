from flask import Blueprint, jsonify

bp = Blueprint("main", __name__)


@bp.route("/", methods=["GET"])
def index():
    """Example route for the main blueprint."""
    return jsonify({"message": "Hello from the main blueprint!"})

