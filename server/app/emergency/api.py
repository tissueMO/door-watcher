###############################################################################
#    システムモード切替用APIを定義します。
###############################################################################
import sys
sys.path.insert(0, ".")
from datetime import datetime as dt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import SingletonThreadPool

# Flask サブモジュールとして必要なパッケージの取り込みと設定を行う
from flask import Blueprint, request, jsonify, Response
from flask_cors import CORS
import app.common as Common
sub_function = Blueprint("emergency", __name__, url_prefix="/emergency")
CORS(sub_function)
logger = Common.get_logger("emergency")


@sub_function.route("/", methods=["PATCH"])
def emergency() -> Response:
    """システムモードの 停止 or 再開 状態を反転させます。

    Returns:
        Response -- application/json = {
            valid: 0 or 1,            // 反転後のステート番号
            action: "停止" or "再開",  // 反転後のステート名
        }
    """
    from model.app_state import AppState
    logger.info(f"[emergency] API Called.")

    with Common.create_session() as session:
        # 現在のシステムモードを取得
        current_state = Common.get_system_mode(session)
        if current_state is None:
            message = "システムモードを取得できませんでした。サーバー上のエラーログを確認して下さい。"
            return jsonify({
                "valid": None,
                "action": message
            })

        # システムモードを反転させて更新
        if current_state == Common.SYSTEM_MODE_STOP:
            next_state = Common.SYSTEM_MODE_RUNNING
            next_state_name = "再開"
        else:
            next_state = Common.SYSTEM_MODE_STOP
            next_state_name = "停止"

        try:
            target_state = session \
                .query(AppState) \
                .filter(AppState.id == Common.SYSTEM_MODE_APP_STATE_ID) \
                .one()
        except NoResultFound:
            message = f"アプリケーション状態マスター id={1} のレコードが設定されていません。"
            logger.error(f"[emergency] API Response. :valid={None} "
                         f":action={message}")
            return jsonify({
                "valid": None,
                "action": message
            })

        target_state.state = next_state
        target_state.modified_time = dt.now()

        session.commit()

    logger.info(f"[emergency] API Response. "\
                f":valid={next_state} :action={next_state_name}")

    return jsonify({
        "valid": next_state,
        "action": next_state_name
    })
