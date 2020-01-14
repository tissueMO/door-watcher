# coding=utf-8
from flask import Blueprint, request, jsonify
fetch = Blueprint("fetch", __name__, url_prefix="/fetch")

@fetch.route("/status", methods=["POST"])
def status():
    return jsonify({})

@fetch.route("/log", methods=["POST"])
def log():
    return jsonify({})
