###############################################################################
#    任意の処理を実行するAPIを定義します。
###############################################################################
import sys
sys.path.insert(0, ".")
from datetime import datetime as dt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool

# Flask サブモジュールとして必要なパッケージの取り込みと設定を行う
from flask import Blueprint, request, jsonify, Response
from flask_cors import CORS
import app.common as Common
action = Blueprint("action", __name__, url_prefix="/action")
CORS(action)
logger = Common.get_logger("action")


@action.route("/open/<int:toilet_id>", methods=["POST"])
def open(toilet_id: int) -> Response:
    """トイレのドアが開いたことを記録します。

    Arguments:
        toilet_id {int} -- ターゲットトイレID

    Returns:
        Response -- application/json = {
            success: True or False,
            message: 補足メッセージ,
        }
    """
    from model.app_state import AppState
    from model.toilet import Toilet
    from model.toilet_status import ToiletStatus
    logger.info(f"[open] API Called. :toilet_id={toilet_id}")

    with Common.create_session() as session:
        current_state = Common.get_system_mode(session)
        if current_state == Common.SYSTEM_MODE_STOP:
            message = "システムモードが停止状態です。すべての入退室ログは記録されません。"
            logger.info(f"[open] API Response. :success={False} "\
                        f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        # 現在の在室状況を取得
        is_closed = session \
            .query(Toilet.is_closed) \
            .filter(Toilet.id == toilet_id) \
            .one() \
            .is_closed
        if not is_closed:
            message = f"トイレ #{toilet_id} は既に空室です。重複防止のため退室ログは記録されません。"
            logger.info(f"[open] API Response. :success={False} "\
                        f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        # 現在の在室状況を更新
        target_toilet = session \
            .query(Toilet) \
            .filter(Toilet.id == toilet_id) \
            .one()
        target_toilet.is_closed = False
        target_toilet.modified_time = dt.now()
        session.add(target_toilet)

        # トイレのドアが開いたことを表すイベントをトランザクションテーブルに追加
        session.add(ToiletStatus(
            toilet_id=toilet_id,
            is_closed=False,
            created_time=dt.now()
        ))

        session.commit()

    message = f"トイレ #{toilet_id} が空室になりました。"
    logger.info(f"[open] API Response. :success={True} "\
                f":message={message}")
    return jsonify({
        "success": True,
        "message": message
    })


@action.route("/close/<int:toilet_id>", methods=["POST"])
def close(toilet_id: int) -> Response:
    """トイレのドアが閉められたことを記録します。

    Arguments:
        toilet_id {int} -- ターゲットトイレID

    Returns:
        Response -- application/json = {
            success: True or False,
            message: 補足メッセージ,
        }
    """
    from model.toilet import Toilet
    from model.toilet_status import ToiletStatus
    logger.info(f"[close] API Called. :toilet_id={toilet_id}")

    with Common.create_session() as session:
        current_state = Common.get_system_mode(session)
        if current_state == Common.SYSTEM_MODE_STOP:
            message = "システムモードが停止状態です。すべての入退室ログは記録されません。"
            logger.info(f"[close] API Response. :success={False} "\
                        f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        # 現在の在室状況を取得
        is_closed = session \
            .query(Toilet.is_closed) \
            .filter(Toilet.id == toilet_id) \
            .one() \
            .is_closed
        if is_closed:
            message = f"トイレ #{toilet_id} は既に使用中です。重複防止のため入室ログは記録されません。"
            logger.info(f"[close] API Response. :success={False} "\
                        f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        # 現在の在室状況を更新
        target_toilet = session \
            .query(Toilet) \
            .filter(Toilet.id == toilet_id) \
            .one()
        target_toilet.is_closed = True
        target_toilet.modified_time = dt.now()
        session.add(target_toilet)

        # トイレのドアが閉められたことを表すイベントをトランザクションテーブルに追加
        session.add(ToiletStatus(
            toilet_id=toilet_id,
            is_closed=True,
            created_time=dt.now()
        ))

        session.commit()

    message = f"トイレ #{toilet_id} が使用中になりました。"
    logger.info(f"[close] API Response. :success={True} "\
                f":message={message}")
    return jsonify({
        "success": True,
        "message": message
    })


@action.route("/emergency", methods=["POST"])
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

        # システムモードを反転させて更新
        if current_state == Common.SYSTEM_MODE_STOP:
            next_state = Common.SYSTEM_MODE_RUNNING
            next_state_name = "再開"
        else:
            next_state = Common.SYSTEM_MODE_STOP
            next_state_name = "停止"

        target_state = session \
            .query(AppState) \
            .filter(AppState.id == Common.SYSTEM_MODE_APP_STATE_ID) \
            .one()
        target_state.state = next_state
        target_state.modified_time = dt.now()

        session.commit()

    logger.info(f"[emergency] API Response. "\
                f":valid={next_state} :action={next_state_name}")

    return jsonify({
        "valid": next_state,
        "action": next_state_name
    })
