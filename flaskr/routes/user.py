from flask import Blueprint,jsonify,request


bp=Blueprint("user",__name__)

@bp.route("/register",methods=["POST"])
def User():
    token = request.get_data(as_text=True)
    print(token)
    return jsonify({
        "success":True,
        "token":token
    })