###############################################################################
#    取得系の処理を実行するAPIを定義します。
###############################################################################
import datetime
from datetime import datetime as dt
from sqlalchemy import create_engine, func, asc, desc
from sqlalchemy.orm import sessionmaker
from flask import Blueprint, request, jsonify, Response
fetch = Blueprint("fetch", __name__, url_prefix="/fetch")

from flask_cors import CORS
CORS(fetch)

@fetch.route("/status", methods=["GET"])
def status():
    """現在のトイレ状況を返します。
    システム停止モードに移行している間はすべて invalid=True の状態として返します。

    Returns:
        Response -- application/json = {
          success: True or False,
          message: "エラーメッセージ",    // エラー発生時のみ
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
    toilets = session \
        .query(
            Toilet,
            func.count().label("max")
        ) \
        .order_by(asc(Toilet.id)) \
        .group_by(Toilet.name) \
        .all()

    # 現在のシステムモードを取得
    current_state = session \
        .query(AppState.state) \
        .filter(AppState.id == 1) \
        .first() \
        .state
    if current_state == 0:
        # 停止モード: すべて無効状態に置き換える
        return jsonify({
            "success": False,
            "message": "現在システムモード「停止」のため、現況を取得できません。\n" +
                       "現況を取得するためにはシステムモード「再開」に切り替えて下さい。"
        })

    # 返却用の形式に変換
    result = {"status": []}
    for i, toilet in enumerate(toilets):
        result["status"].append({
            "name": toilet.Toilet.name,
            "valid": toilet.Toilet.valid,
            "max": toilet.max
        })
        if not toilet.Toilet.valid:
            result["status"][-1]["used"] = 0
        else:
            result["status"][-1]["used"] = session \
                .query(func.count().label("used")) \
                .filter(Toilet.name == toilet[0].name, Toilet.is_closed == True) \
                .first() \
                .used
        result["status"][-1]["rate100"] = \
            int(result["status"][-1]["used"] / toilet.max * 100)

    result["success"] = True
    return jsonify(result)

@fetch.route("/log/<begin_date>/<end_date>/<int:step_minutes>", methods=["GET"])
def log(begin_date: str, end_date: str, step_minutes: int):
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
              "label": "4F男性用トイレ",
              "data": [0, 1, 1, ...]    // 0~1 の使用率を表す
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

    # トイレマスターを取得
    # 非グループ化
    toilets = session \
        .query(Toilet) \
        .all()
    # 名称でグループ化
    grouped_toilets = session \
        .query(
            Toilet,
            func.count().label("max")
        ) \
        .group_by(Toilet.name) \
        .all()

    # 現在のシステムモードを取得
    current_state = session \
        .query(AppState.state) \
        .filter(AppState.id == 1) \
        .first() \
        .state
    if current_state == 0:
        # 停止モード: 空で返す
        return jsonify({})

    # 指定された期間に該当するトイレ入退室トランザクションデータを一括で取得できる原型クエリーを作成
    toilet_statuses_query = session \
        .query(ToiletStatus) \
        .filter(
            begin_datetime <= ToiletStatus.created_time,
            ToiletStatus.created_time < end_datetime
        )

    # それぞれの系列において、指定されたサンプリング間隔で見たときの使用率を算出してデータセットを作る
    labels = []
    datasets = [
      {
        "label": f"{x.Toilet.name}",
        "data": []
      }
      for x in grouped_toilets
    ]

    # ラベルを生成
    current_datetime = begin_datetime
    while current_datetime < end_datetime:
        labels.append(dt.strftime(current_datetime, "%Y-%m-%d %H:%M"))
        current_datetime += datetime.timedelta(minutes=step_minutes)

    # 系列ごとにサンプリングしていく
    for i, series_toilet in enumerate(grouped_toilets):
        # この系列に属するトイレマスターのレコードを抽出
        target_toilets_id_list = [
            x.id for x in toilets if x.name == series_toilet.Toilet.name
        ]
        target_toilets_max = len(target_toilets_id_list)

        # 先頭のサンプリング時刻から一定のサンプリング間隔で状況を抽出していく
        data = []
        current_datetime = begin_datetime
        while current_datetime < end_datetime:
            # 現在のサンプリング時刻の直前にいる対象トイレそれぞれの在室状況を見る
            target_toilets_closed_count = 0

            for target_toilet_id in target_toilets_id_list:
                # NOTE: 万が一取得期間よりも前にしか変更がない場合も考慮して、開始日時は指定しないでおく
                status = toilet_statuses_query \
                    .filter(
                        ToiletStatus.created_time <= current_datetime,
                        ToiletStatus.toilet_id == target_toilet_id
                    ) \
                    .order_by(desc(ToiletStatus.created_time)) \
                    .limit(1) \
                    .first()
                if status is not None:
                    target_toilets_closed_count += (1 if status.is_closed else 0)

            # 現在のサンプリング時刻における使用率を算出
            usage_rate = target_toilets_closed_count / target_toilets_max

            data.append(usage_rate)

            # 次のサンプリング時刻に進める
            current_datetime += datetime.timedelta(minutes=step_minutes)

        # 出来上がった系列データをデータセットに格納
        datasets[i]["data"] = data

    # API側はデータを返すだけで、見た目やオプションはクライアント側で付加してもらうポリシーとする
    return jsonify({
        "labels": labels,
        "datasets": datasets
    })
