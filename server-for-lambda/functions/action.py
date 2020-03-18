###############################################################################
#    任意の処理を実行するAPIを定義します。
###############################################################################
import sys
import json
from datetime import datetime as dt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import SingletonThreadPool

sys.path.insert(0, ".")
import functions.common as Common

### 定数定義
# open/close を許可する最短呼出間隔 (秒)
MIN_DOOR_EVENT_SPAN_SECONDS = 3
# ロガーオブジェクト
logger = Common.get_logger("action")


def open(event, context):
    """トイレのドアが開いたことを記録します。

    Arguments:
        toilet_id {int} -- ターゲットトイレID

    Returns:
        Dict -- application/json = {
            success: True or False,
            message: 補足メッセージ,
        }
    """
    toilet_id = event["toilet_id"]

    from model.app_state import AppState
    from model.toilet import Toilet
    from model.toilet_status import ToiletStatus
    logger.info(f"[open] API Called. :toilet_id={toilet_id}")

    with Common.create_session() as session:
        current_state = Common.get_system_mode(session)
        if current_state is None:
            message = "システムモードを取得できませんでした。サーバー上のエラーログを確認して下さい。"
            return {
                "success": False,
                "message": message
            }
        if current_state == Common.SYSTEM_MODE_STOP:
            message = "システムモードが停止状態です。すべての入退室ログは記録されません。"
            logger.info(f"[open] API Response. :success={False} "\
                        f":message={message}")
            return {
                "success": False,
                "message": message
            }

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
            return {
                "success": False,
                "message": message
            }

        if not is_closed:
            message = f"トイレ #{toilet_id} は既に空室です。重複防止のため退室ログは記録されません。"
            logger.info(f"[open] API Response. :success={False} "\
                        f":message={message}")
            return {
                "success": False,
                "message": message
            }

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
            return {
                "success": False,
                "message": message
            }

        # 前回更新からの経過時間を算出
        timedelta = dt.now() - target_toilet.modified_time
        if timedelta.total_seconds() < MIN_DOOR_EVENT_SPAN_SECONDS:
            message = f"トイレ #{toilet_id} は {MIN_DOOR_EVENT_SPAN_SECONDS} 秒以内に更新されています。"\
                      f"過剰反応防止のため、再度時間を置いてから呼び出して下さい。"
            logger.warning(f"[open] API Response. :success={False} "\
                         f":message={message}")
            return {
                "success": False,
                "message": message
            }

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
    return {
        "success": True,
        "message": message
    }


def close(event, context):
    """トイレのドアが閉められたことを記録します。

    Arguments:
        toilet_id {int} -- ターゲットトイレID

    Returns:
        Dict -- application/json = {
            success: True or False,
            message: 補足メッセージ,
        }
    """
    toilet_id = event["toilet_id"]

    from model.toilet import Toilet
    from model.toilet_status import ToiletStatus
    logger.info(f"[close] API Called. :toilet_id={toilet_id}")

    with Common.create_session() as session:
        current_state = Common.get_system_mode(session)
        if current_state is None:
            message = "システムモードを取得できませんでした。サーバー上のエラーログを確認して下さい。"
            return {
                "success": False,
                "message": message
            }
        if current_state == Common.SYSTEM_MODE_STOP:
            message = "システムモードが停止状態です。すべての入退室ログは記録されません。"
            logger.info(f"[close] API Response. :success={False} "\
                        f":message={message}")
            return {
                "success": False,
                "message": message
            }

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
            return {
                "success": False,
                "message": message
            }

        if is_closed:
            message = f"トイレ #{toilet_id} は既に使用中です。重複防止のため入室ログは記録されません。"
            logger.info(f"[close] API Response. :success={False} "\
                        f":message={message}")
            return {
                "success": False,
                "message": message
            }

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
            return {
                "success": False,
                "message": message
            }

        # 前回更新からの経過時間を算出
        timedelta = dt.now() - target_toilet.modified_time
        if timedelta.total_seconds() < MIN_DOOR_EVENT_SPAN_SECONDS:
            message = f"トイレ #{toilet_id} は {MIN_DOOR_EVENT_SPAN_SECONDS} 秒以内に更新されています。"\
                      f"過剰反応防止のため、再度時間を置いてから呼び出して下さい。"
            logger.warning(f"[close] API Response. :success={False} "\
                         f":message={message}")
            return {
                "success": False,
                "message": message
            }

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
    return {
        "success": True,
        "message": message
    }


def emergency(event, context):
    """システムモードの 停止 or 再開 状態を反転させます。

    Returns:
        Dict -- application/json = {
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
            return {
                "valid": None,
                "action": message
            }

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
            return {
                "valid": None,
                "action": message
            }

        target_state.state = next_state
        target_state.modified_time = dt.now()

        session.commit()

    logger.info(f"[emergency] API Response. "\
                f":valid={next_state} :action={next_state_name}")

    return {
        "valid": next_state,
        "action": next_state_name
    }
