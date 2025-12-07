from flask import Blueprint, jsonify, request

bp = Blueprint("payments", __name__)


@bp.route("/", methods=["POST"])
def process_payment():
    """Example payments route."""
    payload = request.get_json(silent=True) or {}
    total = payload.get("amount", 0)
    return jsonify({"status": "processed", "amount": total})


