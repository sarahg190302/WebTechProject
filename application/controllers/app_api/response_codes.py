from flask import jsonify, make_response

def show_200(msg="success"):
        return make_response(jsonify({"msg": msg}), 200)

def show_404(msg = "The requested resource was not found on this server"):
    return make_response(jsonify({"msg": msg}), 404)

def show_500():
    return make_response(jsonify({"msg": "Internal server error occurred"}), 500)

def show_400(msg = "Bad Request sent"):
    return make_response(jsonify({"msg": msg}), 400)