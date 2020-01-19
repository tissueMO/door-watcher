###############################################################################
#    任意の処理を実行するAPIを定義します。
###############################################################################
import sys
sys.path.insert(0, ".")
from datetime import datetime as dt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool
from flask import Blueprint, request, jsonify, Response
action = Blueprint("action", __name__, url_prefix="/action")

from flask_cors import CORS
CORS(action)

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
    print(toilet_id)

    # セッション作成
    engine = create_engine("sqlite:///db/toilet.db", poolclass=SingletonThreadPool)
    session = sessionmaker(bind=engine)()

    # 現在のシステムモードを取得
    current_state = session.query(AppState.state).filter(AppState.id == 1).one()[0]
    if current_state == 0:
        # 停止モード
        message = "システムモードが停止状態です。すべての入退室ログは記録されません。"
        return jsonify({
            "success": False,
            "message": message
        })

    # 現在の在室状況を取得
    is_closed = session.query(Toilet.is_closed).filter(Toilet.id == toilet_id).one()[0]
    if not is_closed:
        # 既に空室なので変化なし
        message = f"トイレ #{toilet_id} は既に空室です。重複防止のため退室ログは記録されません。"
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
    return jsonify({
        "success": True,
        "message": f"トイレ #{toilet_id} が空室になりました。"
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
    from model.app_state import AppState
    from model.toilet import Toilet
    from model.toilet_status import ToiletStatus
    print(toilet_id)

    # セッション作成
    engine = create_engine("sqlite:///db/toilet.db")
    session = sessionmaker(bind=engine)()

    # 現在のシステムモードを取得
    current_state = session.query(AppState.state).filter(AppState.id == 1).one()[0]
    if current_state == 0:
        # 停止モード
        message = "システムモードが停止状態です。すべての入退室ログは記録されません。"
        return jsonify({
            "success": False,
            "message": message
        })

    # 現在の在室状況を取得
    is_closed = session.query(Toilet.is_closed).filter(Toilet.id == toilet_id).one()[0]
    if is_closed:
        # 既に使用中なので変化なし
        message = f"トイレ #{toilet_id} は既に使用中です。重複防止のため入室ログは記録されません。"
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
    return jsonify({
        "success": True,
        "message": f"トイレ #{toilet_id} が使用中になりました。"
    })

@action.route("/emergency", methods=["POST"])
def emergency() -> Response:
    """システムモードの 停止 or 再開 状態を反転させます。

    Returns:
        Response -- application/json = {
            valid: 0 or 1,
            action: "停止" or "再開",
        }
    """
    from model.app_state import AppState

    # セッション作成
    engine = create_engine("sqlite:///db/toilet.db")
    session = sessionmaker(bind=engine)()

    # 現在の緊急停止モードを取得
    current_state = session \
        .query(AppState.state) \
        .filter(AppState.id == 1) \
        .first() \
        .state

    # 緊急停止モードを更新
    if current_state == 1:
        next_state = 0
        next_state_name = "停止"
    else:
        next_state = 1
        next_state_name = "再開"

    target_state = session \
        .query(AppState) \
        .filter(AppState.id == 1) \
        .one()
    target_state.state = next_state
    target_state.modified_time = dt.now()

    session.commit()
    return jsonify({
        "valid": next_state,
        "action": next_state_name
    })
