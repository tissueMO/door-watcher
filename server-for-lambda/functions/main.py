###############################################################################
#    WSGI Webアプリケーションを定義します。
#    このスクリプトを単体で起動した場合は Flask 内蔵サーバーで立ち上がります。
###############################################################################
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

import sys
sys.path.insert(0, ".")

# 各種サブモジュールをロード
from app.action import action
from app.fetch import fetch
app.register_blueprint(action)
app.register_blueprint(fetch)


@app.route("/health", methods=["GET"])
def health():
    """ヘルスチェック用API
    このAPIをパスすると常にステータスコード200を返します。
    万が一200以外を返した場合は何らかのサーバー障害が起きていることを表します。

    Returns:
        Response -- application/json = {}
    """
    return jsonify({})


if __name__ == "__main__":
    # 単体起動した場合は Flask 内蔵サーバーを立ち上げる
    app.run(host="0.0.0.0", port=3000)
