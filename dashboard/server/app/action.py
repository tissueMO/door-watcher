# coding=utf-8
from flask import Blueprint, request, jsonify
action = Blueprint("action", __name__, url_prefix="/action")

@action.route("/emergency", methods=["POST"])
def emergency():
    return jsonify({})
