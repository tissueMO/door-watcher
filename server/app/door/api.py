###############################################################################
#    ドアステート切替用APIを定義します。
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
sub_function = Blueprint("door", __name__, url_prefix="/door")
CORS(sub_function)
logger = Common.get_logger("door")

### 定数定義
# open/close を許可する最短呼出間隔 (秒)
MIN_DOOR_EVENT_SPAN_SECONDS = 3


@sub_function.route("/open", methods=["PUT"])
def open() -> Response:
    """トイレのドアが開いたことを記録します。

    Arguments:
        toilet_id {int} -- ターゲットトイレID

    Returns:
        Response -- application/json = {
            success: True or False,
            message: 補足メッセージ,
        }
    """
    toilet_id = request.json["toilet_id"]

    from model.app_state import AppState
    from model.toilet import Toilet
    from model.toilet_status import ToiletStatus
    logger.info(f"[open] API Called. :toilet_id={toilet_id}")

    with Common.create_session() as session:
        current_state = Common.get_system_mode(session)
        if current_state is None:
            message = "システムモードを取得できませんでした。サーバー上のエラーログを確認して下さい。"
            return jsonify({
                "success": False,
                "message": message
            })
        if current_state == Common.SYSTEM_MODE_STOP:
            message = "システムモードが停止状態です。すべての入退室ログは記録されません。"
            logger.info(f"[open] API Response. :success={False} "\
                        f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        # 現在の在室状況を取得
        try:
            is_closed = session \
                .query(Toilet.is_closed) \
                .filter(Toilet.id == toilet_id) \
                .one() \
                .is_closed
        except NoResultFound:
            message = f"トイレ #{toilet_id} が見つかりません。トイレマスター上のID設定とAPI呼び出し元のIDが合致することを確認して下さい。"
            logger.error(f"[open] API Response. :success={False} "\
                         f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        if not is_closed:
            message = f"トイレ #{toilet_id} は既に空室です。重複防止のため退室ログは記録されません。"
            logger.info(f"[open] API Response. :success={False} "\
                        f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        # 現在の在室状況を更新
        try:
            target_toilet = session \
                .query(Toilet) \
                .filter(Toilet.id == toilet_id) \
                .one()
        except NoResultFound:
            message = f"トイレ #{toilet_id} が見つかりません。トイレマスター上のID設定とAPI呼び出し元のIDが合致することを確認して下さい。"
            logger.error(f"[open] API Response. :success={False} "\
                         f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        # 前回更新からの経過時間を算出
        timedelta = dt.now() - target_toilet.modified_time
        if timedelta.total_seconds() < MIN_DOOR_EVENT_SPAN_SECONDS:
            message = f"トイレ #{toilet_id} は {MIN_DOOR_EVENT_SPAN_SECONDS} 秒以内に更新されています。"\
                      f"過剰反応防止のため、再度時間を置いてから呼び出して下さい。"
            logger.warning(f"[open] API Response. :success={False} "\
                         f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

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


@sub_function.route("/close", methods=["PUT"])
def close() -> Response:
    """トイレのドアが閉められたことを記録します。

    Arguments:
        toilet_id {int} -- ターゲットトイレID

    Returns:
        Response -- application/json = {
            success: True or False,
            message: 補足メッセージ,
        }
    """
    toilet_id = request.json["toilet_id"]

    from model.toilet import Toilet
    from model.toilet_status import ToiletStatus
    logger.info(f"[close] API Called. :toilet_id={toilet_id}")

    with Common.create_session() as session:
        current_state = Common.get_system_mode(session)
        if current_state is None:
            message = "システムモードを取得できませんでした。サーバー上のエラーログを確認して下さい。"
            return jsonify({
                "success": False,
                "message": message
            })
        if current_state == Common.SYSTEM_MODE_STOP:
            message = "システムモードが停止状態です。すべての入退室ログは記録されません。"
            logger.info(f"[close] API Response. :success={False} "\
                        f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        # 現在の在室状況を取得
        try:
            is_closed = session \
                .query(Toilet.is_closed) \
                .filter(Toilet.id == toilet_id) \
                .one() \
                .is_closed
        except NoResultFound:
            message = f"トイレ #{toilet_id} が見つかりません。トイレマスター上のID設定とAPI呼び出し元のIDが合致することを確認して下さい。"
            logger.error(f"[close] API Response. :success={False} "\
                         f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        if is_closed:
            message = f"トイレ #{toilet_id} は既に使用中です。重複防止のため入室ログは記録されません。"
            logger.info(f"[close] API Response. :success={False} "\
                        f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        # 現在の在室状況を更新
        try:
            target_toilet = session \
                .query(Toilet) \
                .filter(Toilet.id == toilet_id) \
                .one()
        except NoResultFound:
            message = f"トイレ #{toilet_id} が見つかりません。トイレマスター上のID設定とAPI呼び出し元のIDが合致することを確認して下さい。"
            logger.error(f"[close] API Response. :success={False} "\
                         f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        # 前回更新からの経過時間を算出
        timedelta = dt.now() - target_toilet.modified_time
        if timedelta.total_seconds() < MIN_DOOR_EVENT_SPAN_SECONDS:
            message = f"トイレ #{toilet_id} は {MIN_DOOR_EVENT_SPAN_SECONDS} 秒以内に更新されています。"\
                      f"過剰反応防止のため、再度時間を置いてから呼び出して下さい。"
            logger.warning(f"[close] API Response. :success={False} "\
                         f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

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
