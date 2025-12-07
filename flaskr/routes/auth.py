from flask import Blueprint, jsonify, request

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["POST"])
def login():
    """Example auth route."""
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "guest")
    return jsonify({"message": f"Logged in as {username}"}), 200

