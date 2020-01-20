###############################################################################
#    取得系の処理を実行するAPIを定義します。
###############################################################################
import sys
sys.path.insert(0, ".")
import datetime
from datetime import datetime as dt
from sqlalchemy import func, asc, desc

# Flask サブモジュールとして必要なパッケージの取り込みと設定を行う
from flask import Blueprint, request, jsonify, Response
from flask_cors import CORS
import app.common as Common
fetch = Blueprint("fetch", __name__, url_prefix="/fetch")
CORS(fetch)
logger = Common.get_logger("fetch")


@fetch.route("/status", methods=["GET"])
def status():
    """現在のトイレ在室状況を返します。
    なお、システム停止モードに移行している間はすべて success=False として返します。

    Returns:
        Response -- application/json = {
          success: True or False,
          message: "エラーメッセージ",    // エラー発生時のみ。正常完了時は空文字
          status: [
            {
              name: "4F 男性用トイレ",   // トイレの名称
              valid: True or False,    // このトイレグループの状況を取得できたかどうか
              used: 1,                 // このトイレグループにおける現在の使用数
              max: 2,                  // このトイレグループの部屋数
              rate100: 0-100,          // このトイレグループの使用率% (同じ名前のトイレを合算した使用率%)
            },
            ...
          ]
        }
    """
    from model.toilet import Toilet
    logger.info(f"[status] API Called.")

    with Common.create_session() as session:
        # トイレマスターを取得: 名称でグループ化
        toilets = session \
            .query(
                Toilet,
                func.count().label("max")
            ) \
            .order_by(asc(Toilet.id)) \
            .group_by(Toilet.name) \
            .all()

        current_state = Common.get_system_mode(session)
        if current_state == Common.SYSTEM_MODE_STOP:
            message = "現在システムモード「停止」のため、現況を取得できません。"\
                      "現況を取得するためにはシステムモード「再開」に切り替えて下さい。"
            logger.info(f"[status] API Response. :success={False} "\
                        f":message={message}")
            return jsonify({
                "success": False,
                "message": message
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
                    .filter(
                        Toilet.name == toilet[0].name,
                        Toilet.is_closed == True
                    ) \
                    .first() \
                    .used
            result["status"][-1]["rate100"] = \
                int(result["status"][-1]["used"] / toilet.max * 100)

    result["success"] = True
    result["message"] = ""
    logger.info(f"[status] API Response. :success={True} :status_length={len(result['status'])}")
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
          "success": True of False,
          "message": 補足メッセージ,        // エラー発生時のみ。正常完了時は空文字
          "graphs": [
            {
              "type": "bar",
              "data": {
                "labels": [
                  "2019-01-01 00:00", "2019-01-01 00:05", ..., "2019-01-02 00:00", ...
                ],
                "datasets": [
                  {
                    "label": "4F 男性用トイレ",
                    "data": [0, 1, 1, ...]    // それぞれの単位時間内におけるオープン、クローズのイベント数合計値
                  }
                ]
              }
            },
            ...
          ]
        }
    """
    from model.toilet import Toilet
    from model.toilet_status import ToiletStatus
    logger.info(f"[log] API Called. "\
                f":begin_date={begin_date} :end_date={end_date} :step_minutes={step_minutes}")

    # パラメーター形式変換
    begin_datetime = dt.strptime(begin_date, Common.PARAM_DATETIME_FORMAT)
    end_datetime = dt.strptime(end_date, Common.PARAM_DATETIME_FORMAT)

    with Common.create_session() as session:
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
            .order_by(asc(Toilet.id)) \
            .all()

        current_state = Common.get_system_mode(session)
        if current_state == Common.SYSTEM_MODE_STOP:
            message = "システムモードが停止状態です。入退室ログは返却しません。"
            logger.info(f"[log] API Response. :success={False} "\
                        f":message={message}")
            return jsonify({
                "success": False,
                "message": message
            })

        # 横軸ラベルを生成
        graphs = []
        labels = []
        current_datetime = begin_datetime
        while current_datetime < end_datetime:
            labels.append(dt.strftime(current_datetime, "%Y-%m-%d %H:%M"))
            current_datetime += datetime.timedelta(minutes=step_minutes)

        # 系列ごとにグラフデータを分けて作成
        for i, series_toilet in enumerate(grouped_toilets):
            graph = {
              "type": "bar",
              "data": {
                "labels": labels,
                "datasets": [{
                  "label": series_toilet.Toilet.name,
                  "data": []
                }]
              }
            }

            # この系列に属するトイレマスターのレコードを抽出
            target_toilets_id_list = [
                x.id
                for x in toilets
                if x.name == series_toilet.Toilet.name
            ]

            # この系列に属するトイレ入退室トランザクションテーブルで区間内に該当するレコードを抽出
            target_statuses_all = session \
                .query(ToiletStatus) \
                .filter(
                    begin_datetime <= ToiletStatus.created_time,
                    ToiletStatus.created_time < end_datetime,
                    ToiletStatus.toilet_id.in_(target_toilets_id_list)
                ) \
                .order_by(asc(ToiletStatus.created_time)) \
                .all()

            # 先頭のサンプリング時刻から一定のサンプリング間隔でレコードを抽出していく
            data = []
            delta_datetime = datetime.timedelta(minutes=step_minutes)
            current_datetime = begin_datetime + delta_datetime
            start_index = 0
            while current_datetime < end_datetime + delta_datetime:
                sampling_count = 0
                for n, target_status in enumerate(target_statuses_all[start_index:]):
                    if target_status.created_time < current_datetime:
                      # 対象区間内のレコードであればカウント
                      sampling_count += 1
                    else:
                      # 対象区間から出た時点で抜ける
                      start_index = n
                      break

                data.append(sampling_count)

                # 次のサンプリング時刻に進める
                current_datetime += delta_datetime

            # 出来上がったグラフデータをグラフリストに格納
            graph["data"]["datasets"][0]["data"] = data
            graphs.append(graph)

    # API側はデータを返すだけで、見た目やオプションはクライアント側で付加してもらうポリシーとする
    result = {
        "success": True,
        "message": "",
        "graphs": graphs
    }
    logger.info(f"[log] API Response. :success={True} :graphs_length={len(graphs)}")
    return jsonify(result)
