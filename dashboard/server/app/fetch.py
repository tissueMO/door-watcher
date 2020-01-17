###############################################################################
#    取得系の処理を実行するAPIを定義します。
###############################################################################
import datetime
from datetime import datetime as dt
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from flask import Blueprint, request, jsonify, Response
fetch = Blueprint("fetch", __name__, url_prefix="/fetch")

@fetch.route("/status", methods=["GET"])
def status():
    """現在のトイレ状況を返します。
    システム停止モードに移行している間はすべて invalid=True の状態として返します。

    Returns:
        Response -- application/json = {
          status: [
            {
              name: "4F男性用トイレ",    // トイレの名称
              valid: True or False,    // このトイレの状況を取得できたかどうか
              used: 1,                 // このトイレにおける現在の使用数
              max: 2,                  // このトイレ全体の室数
              rate100: 0-100,          // このトイレの使用率% (同じ名前のトイレを合算した使用率%)
            },
            ...
          ]
        }
    """
    from model.app_state import AppState
    from model.toilet import Toilet

    # セッション作成
    engine = create_engine("sqlite:///db/toilet.db")
    session = sessionmaker(bind=engine)()

    # トイレマスターを取得: 名称でグループ化
    toilets = session
        .query(
            Toilet,
            func.count().label("max")
        )
        .group_by(Toilet.name)
        .all()

    # 現在のシステムモードを取得
    current_state = session
        .query(AppState.state)
        .filter(AppState.id == 1)
        .first()[0]
    if current_state == 0:
        # 停止モード: すべて無効状態に置き換える
        for i, toilet in enumerate(toilets):
            toilet.valid = False

    # 返却用の形式に変換
    result = {status: []}
    for i, toilet in enumerate(toilets):
        result["status"].append({
            name: toilet.name,
            valid: toilet.valid,
            max: toilet.max
        })
        result["status"][-1]["used"] = \
            session
                .query(Toilet)
                .filter(Toilet.name == toilet[0].name, Toilet.is_closed == True)
                .count()
        result["status"][-1]["rate100"] = \
            int(toilet.used / toilet.max * 100)

    return jsonify(result)

@fetch.route("/log/<begin_date>/<end_date>/<int:step_minutes>", methods=["GET"])
def log(start_date: str, end_date: str, step_minutes: int):
    """指定期間における全トイレの使用率の推移を表したデータを返します。

    Arguments:
        begin_date {str} -- 期間開始日 (%Y%m%d)
        end_date {str} -- 期間終了日 (%Y%m%d)
        step_minutes {int} -- 期間内におけるサンプリング間隔 (分)

    Returns:
        Response -- application/json = {
          "labels": [
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
    from model.app_state import AppState
    from model.toilet import Toilet
    from model.toilet_status import ToiletStatus

    # パラメーター形式変換
    begin_datetime = dt.strptime(begin_date, "%Y%m%d")
    end_datetime = dt.strptime(end_date, "%Y%m%d")

    # セッション作成
    engine = create_engine("sqlite:///db/toilet.db")
    session = sessionmaker(bind=engine)()

    # トイレマスターを取得: 名称でグループ化
    toilets = session
        .query(
            Toilet,
            func.count().label("max")
        )
        .group_by(Toilet.name)
        .all()

    # 現在のシステムモードを取得
    current_state = session
        .query(AppState.state)
        .filter(AppState.id == 1)
        .first()[0]
    if current_state == 0:
        # 停止モード: 空で返す
        return jsonify({})

    # 指定された期間に該当するトイレ入退室トランザクションデータを一括で取得
    toilet_statuses = session
        .query(ToiletStatus)
        .filter(
            begin_datetime <= ToiletStatus.created_time,
            ToiletStatus.created_time < end_datetime
        ).all()

    # それぞれの系列において、指定されたサンプリング間隔で見たときの使用率を算出してデータセットを作る
    labels = []
    datasets = []
    current_datetime = begin_datetime

    while current_datetime < end_datetime:

        # 次のサンプリング時刻に進める
        current_datetime + datetime.timedelta(minutes=step_minutes)

    # API側はデータを返すだけで、見た目やオプションはクライアント側で付加してもらうポリシーとする
    return jsonify({
        labels: labels,
        datasets: datasets
    })
