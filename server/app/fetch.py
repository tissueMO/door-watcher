###############################################################################
#    取得系の処理を実行するAPIを定義します。
###############################################################################
import sys
sys.path.insert(0, ".")
import datetime
from datetime import datetime as dt
from sqlalchemy import func, asc, desc
from sqlalchemy.orm.exc import NoResultFound

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
        if current_state is None:
            message = "システムモードを取得できませんでした。サーバー上のエラーログを確認して下さい。"
            return jsonify({
                "success": False,
                "message": message
            })
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
                try:
                    result["status"][-1]["used"] = session \
                        .query(func.count().label("used")) \
                        .filter(
                            Toilet.name == toilet[0].name,
                            Toilet.is_closed == True
                        ) \
                        .one() \
                        .used
                except NoResultFound:
                    logger.warning(f"[status] API Error. トイレ [{toilet[0].name}] のレコード数の取得に失敗しました。トイレマスターの定義を確認して下さい。")
                    result["status"][-1]["used"] = 0

            result["status"][-1]["rate100"] = \
                int(result["status"][-1]["used"] / toilet.max * 100)

    result["success"] = True
    result["message"] = ""
    logger.info(f"[status] API Response. :success={True} :status_length={len(result['status'])}")
    return jsonify(result)


@fetch.route("/log/<begin_date>/<end_date>/<int:begin_hours_per_day>/<int:end_hours_per_day>/<int:step_hours>", methods=["GET"])
def log(begin_date: str, end_date: str, begin_hours_per_day: int, end_hours_per_day: int, step_hours: int):
    """指定期間、および日当たりそれぞれの時間帯におけるすべてのトイレの使用回数を表す Chart.js グラフ用データを返します。
    このAPIでは、ドアが閉じられた回数をもとに集計します。

    Arguments:
        begin_date {str} -- 期間開始日 (%Y%m%d)
        end_date {str} -- 期間終了日 (%Y%m%d)
        begin_hours_per_day {int} -- 日当たりの集計始端時間 (0-23)
        end_hours_per_day {int} -- 日当たりの集計終端時間 (0-23)
        step_hours {int} -- 期間内におけるサンプリング間隔 (1-24)、始端時間から終端時間の差をこの値で割り切れない場合は割り切れる時間まで延長します。

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
                f":begin_date={begin_date} :end_date={end_date} "\
                f":begin_hours_per_day={begin_hours_per_day} :end_hours_per_day={end_hours_per_day} "\
                f":step_hours={step_hours}")

    # パラメーター形式変換
    begin_datetime = dt.strptime(begin_date, Common.PARAM_DATETIME_FORMAT)
    end_datetime = dt.strptime(end_date, Common.PARAM_DATETIME_FORMAT)
    if end_datetime < begin_datetime:
        # 始端日と終端日の指定が逆になっていると判断
        temp = begin_datetime
        begin_datetime = end_datetime
        end_datetime = temp
        logger.warning(f"[log] API Parameter Check. :begin_datetime={end_datetime}->{begin_datetime} "\
                       f":end_datetime={begin_datetime}->{end_datetime}")
    if end_hours_per_day < begin_hours_per_day:
        # 始端時間と終端時間の指定が逆になっていると判断
        temp = begin_hours_per_day
        begin_hours_per_day = end_hours_per_day
        end_hours_per_day = temp
        logger.warning(f"[log] API Parameter Check. :begin_hours_per_day={end_hours_per_day}->{begin_hours_per_day} "\
                       f":end_hours_per_day={begin_hours_per_day}->{end_hours_per_day}")
    if (end_hours_per_day - begin_hours_per_day) < step_hours:
        # サンプリング間隔は始端時間と終端時間の差を超えることはできない: 日単位とする
        raw_step_hours = step_hours
        step_hours = end_hours_per_day - begin_hours_per_day
        logger.warning(f"[log] API Parameter Check. :step_hours={raw_step_hours}->{step_hours}")
    elif step_hours <= 0:
        # サンプリング間隔が正しくない場合はデフォルトで3時間刻みとする
        raw_step_hours = step_hours
        step_hours = 3
        logger.warning(f"[log] API Parameter Check. :step_hours={raw_step_hours}->{step_hours}")

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
        if current_state is None:
            message = "システムモードを取得できませんでした。サーバー上のエラーログを確認して下さい。"
            return jsonify({
                "success": False,
                "message": message
            })
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
        target_begin_and_end_pairs = []
        current_begin_hours = begin_hours_per_day
        current_end_hours = current_begin_hours + step_hours
        current_datetime = begin_datetime

        while current_datetime < end_datetime:
            current_begin_datetime = current_datetime + datetime.timedelta(hours=current_begin_hours)
            current_end_datetime = current_datetime + datetime.timedelta(hours=current_end_hours)
            target_begin_and_end_pairs.append({
                "begin": current_begin_datetime,
                "end": current_end_datetime
            })
            labels.append(
                f"{dt.strftime(current_begin_datetime, '%m-%d %H:%M')}~"\
                f"{dt.strftime(current_end_datetime, '%H:%M')}"
            )

            if end_hours_per_day <= current_end_hours:
                # 次の日へ回す
                current_begin_hours = begin_hours_per_day
                current_datetime += datetime.timedelta(days=1)
            else:
                current_begin_hours += step_hours
            current_end_hours = current_begin_hours + step_hours

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

            # 先頭のサンプリング時間から順にドアクローズイベントの件数を抽出していく
            data = []
            start_index = 0
            for one_of_begin_and_end_pairs in target_begin_and_end_pairs:
                sampling_count = 0

                for n, target_status in enumerate(target_statuses_all[start_index:]):
                    if one_of_begin_and_end_pairs["begin"] <= target_status.created_time and \
                            target_status.created_time < one_of_begin_and_end_pairs["end"]:
                        # 対象区間内のレコードであればカウント
                        sampling_count += 1
                    elif one_of_begin_and_end_pairs["end"] <= target_status.created_time:
                        # 対象区間から出た時点で抜ける
                        start_index = n
                        break

                data.append(sampling_count)

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
