###############################################################################
#    任意の処理を実行するAPIを定義します。
###############################################################################
from flask import Blueprint, request, jsonify, Response
action = Blueprint("action", __name__, url_prefix="/action")

@action.route("/emergency", methods=["POST"])
def emergency() -> Response:
    """緊急停止 or 再開

    Returns:
        Response -- application/json = {
            valid: 0 or 1,
            action: "停止" or "再開",
        }
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    engine = create_engine("sqlite:///../db/toilet.db")

    with engine.connect() as connect:
        # 現在状況を取得

        # トイレマスター
        connect.execute(f"INSERT INTO toilet (id, name, valid, room_count) VALUES " +
                        f"(1, '4F男性用トイレ', 1, 1)")
        connect.execute(f"INSERT INTO toilet (id, name, valid, room_count) VALUES " +
                        f"(2, '6F男性用トイレ', 1, 1)")
        connect.execute(f"INSERT INTO toilet (id, name, valid, room_count) VALUES " +
                        f"(3, '4F女性用トイレ', 1, 2)")
        connect.execute(f"INSERT INTO toilet (id, name, valid, room_count) VALUES " +
                        f"(4, '6F女性用トイレ', 1, 2)")

        # アプリケーション状態マスター
        connect.execute(f"INSERT INTO app_state (id, name, state, comment, modified_time) VALUES "
                        f"(1, '緊急停止モード', 0, 'すべて使用できない状態にします', '2020-01-01 00:00:00')")

    return jsonify({
        valid: 0,
        action: ""
    })
