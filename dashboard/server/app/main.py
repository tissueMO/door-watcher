#! /usr/bin/env python
from flask import Flask, request, jsonify
app = Flask(__name__)

# 各種サブモジュールをロード
from app.action import action
from app.fetch import fetch
app.register_blueprint(action)
app.register_blueprint(fetch)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({})


if __name__ == "__main__":
    app.run(host="0.0.0.0")
