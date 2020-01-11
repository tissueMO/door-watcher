# coding=utf-8

from flask import request, jsonify
from app import app

@app.route("/fetch/status", methods=["POST"])
def fetch_status():
    return jsonify({})

@post("/fetch/log", methods=["POST"])
def fetch_log():
    return jsonify({})

@post("/action/emergency", methods=["POST"])
def action_emergency():
    return jsonify({})

@post("/health", methods=["GET"])
def health():
    return jsonify({})
