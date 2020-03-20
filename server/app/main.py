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
from app import api
from app.door import api as door
from app.emergency import api as emergency
from app.logs import api as logs
app.register_blueprint(door.sub_function)
app.register_blueprint(emergency.sub_function)
app.register_blueprint(logs.sub_function)


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
