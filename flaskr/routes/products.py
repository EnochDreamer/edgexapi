from flask import Blueprint, jsonify

bp = Blueprint("products", __name__)


@bp.route("/", methods=["GET"])
def list_products():
    """Example products route."""
    sample_products = [
        {"id": 1, "name": "Widget"},
        {"id": 2, "name": "Gadget"},
    ]
    return jsonify(sample_products)


