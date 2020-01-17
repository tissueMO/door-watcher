###############################################################################
#    取得系の処理を実行するAPIを定義します。
###############################################################################
from flask import Blueprint, request, jsonify, Response
fetch = Blueprint("fetch", __name__, url_prefix="/fetch")

@fetch.route("/status", methods=["GET"])
def status():
    """[summary]

    Returns:
        [type] -- [description]
    """
    return jsonify({})

@fetch.route("/log", methods=["GET"])
def log():
    """[summary]

    Returns:
        [type] -- [description]
    """
"""
# Chart.js 仕様のI/F 定義案: API側はデータを返すだけ、見た目やオプションはクライアント側で付加してもらうポリシーで
json = {
  "labels": [
    # TODO: 刻み分数と取得期間を決められるようにする？ デフォルトは1か月の5分刻みで
    "2019-01-01 00:00", "2019-01-01 00:05", ..., "2019-01-02 00:00", ...
  ],
  "datasets": [
    {
      "label": "4F男性用トイレ(空き)",
      "data": [0, 1, 1, ...]
    },
    ...
  ]
}
"""
    return jsonify({})
