from flask import Blueprint, jsonify, request, current_app
from ..models.user import User
from ..extensions import db
from flaskr.auth import verify_decode_jwt 


bp = Blueprint("user", __name__)


@bp.route("/register", methods=["POST"])
def register():
    """Handle Kinde webhook events on the /register endpoint.

    Only handles:
      - user.created -> create user if not exists
      - user.deleted -> delete user by email if exists

    No updates are performed.

    """
    token = request.get_data(as_text=True)
    print(token)
    payload = verify_decode_jwt(token, allow_signature_only=True)
    if not payload:
        return jsonify({"success": False, "error": "Invalid JSON"}), 400

    event_type = payload.get('type')
    data = payload.get('data') or {}
    user = data.get('user') if isinstance(data, dict) else None

    if event_type == 'user.created' and user:
        email = user.get('email')
        first_name = user.get('first_name')
        last_name = user.get('last_name')
        username = user.get('username')

        if not email:
            return jsonify({"success": False, "error": "User email missing"}), 400

        try:
            if User.query.filter_by(email=email).one_or_none():
                # Do not perform updates per request
                return jsonify({"success": False, "error": "User already exists"}), 409

            base_username = (username or ((first_name or '') + (last_name or '')) or email.split('@')[0])
            base_username = base_username.replace(' ', '_')[:80]
            candidate = base_username
            i = 1
            while User.query.filter_by(username=candidate).first():
                candidate = f"{base_username}_{i}"[:80]
                i += 1
            user_obj = User(username=candidate, email=email)
            db.session.add(user_obj)
            db.session.commit()
            return jsonify({"success": True, "user": {"id": user_obj.id, "username": user_obj.username, "email": user_obj.email}})
        except Exception:
            current_app.logger.exception('Failed to create user from webhook')
            return jsonify({"success": False, "error": "Database error"}), 500

    if event_type == 'user.deleted' and user:
        email = user.get('email')
        if not email:
            return jsonify({"success": False, "error": "User email missing for delete"}), 400
        try:
            existing = User.query.filter_by(email=email).first()
            if not existing:
                return jsonify({"success": False, "error": "User not found"}), 404
            existing.remove()
            return jsonify({"success": True, "deleted_email": email})
        except Exception:
            current_app.logger.exception('Failed to delete user from webhook')
            return jsonify({"success": False, "error": "Database error"}), 500

    return jsonify({"success": False, "error": "Unsupported event or missing user"}), 400
