from flask import Blueprint,jsonify


bp=Blueprint("user",__name__)

@bp.route("/register",methods=["GET"])
def User():
    return jsonify({
        "success":True
    })