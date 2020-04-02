###############################################################################
#    ログ取得APIを定義します。
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
sub_function = Blueprint("logs", __name__, url_prefix="/logs")
CORS(sub_function)
logger = Common.get_logger("logs")


@sub_function.route("/", methods=["GET"])
def log():
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
                    "label": "4F 男性用トイレ - N時間あたりの使用頻度",  // トイレグループ単位
                    "data": [0, 1, 1, ...]    // それぞれの単位時間内におけるドアクローズのイベント数合計値
                  }
                ]
              }
            },
            ...,
            {
              "type": "bar",
              "data": {
                "labels": [ 省略 ],
                "datasets": [
                  {
                    "label": "4F 男性用トイレ - N時間あたりの占有率",  // トイレグループ単位
                    "data": [0.25, 1.0, 0, ...]    // それぞれの単位時間内におけるオープン、クローズのイベント数合計値
                  }
                ]
              }
            },
            ...
          ]
        }
    """
    end_date_default = dt.now()
    begin_date_default = end_date_default - datetime.timedelta(days=10)
    begin_date = request.args.get("begin_date", dt.strftime(begin_date_default, Common.PARAM_DATETIME_FORMAT))
    end_date = request.args.get("end_date", dt.strftime(end_date_default, Common.PARAM_DATETIME_FORMAT))
    begin_hours_per_day = request.args.get("begin_hours_per_day", 10, type=int)
    end_hours_per_day = request.args.get("end_hours_per_day", 19, type=int)
    step_hours = request.args.get("step_hours", 2, type=int)

    from model.toilet import Toilet
    from model.toilet_group import ToiletGroup
    from model.toilet_group_map import ToiletGroupMap
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

    # 日付計算の都合上、終端日時は 24:00 とする
    end_datetime = end_datetime + datetime.timedelta(hours=24)

    with Common.create_session() as session:
        # トイレマスターを取得
        toilets = session \
            .query( \
                Toilet,
                ToiletGroupMap
            ) \
            .outerjoin(ToiletGroupMap, Toilet.id == ToiletGroupMap.toilet_id) \
            .all()

        # トイレグループマスターを取得: トイレへの紐付け情報も合わせて取得
        grouped_toilets = session \
            .query(
                ToiletGroup,
                ToiletGroupMap,
                func.count().label("max")
            ) \
            .outerjoin(ToiletGroupMap, ToiletGroup.id == ToiletGroupMap.toilet_group_id) \
            .order_by(asc(ToiletGroup.id)) \
            .group_by(ToiletGroup.id) \
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

        ##### 使用頻度 (抽出開始時刻よりも前から継続して入室中だったデータはカウント対象に含まれないので注意) #####
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
                  "label": f"{series_toilet.ToiletGroup.name} - {step_hours}時間あたりの使用頻度",
                  "data": []
                }]
              }
            }

            # この系列に属するトイレマスターのレコードを抽出
            target_toilets_id_list = [
                x.Toilet.id
                for x in toilets
                if x.ToiletGroupMap.toilet_group_id == series_toilet.ToiletGroupMap.toilet_group_id
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
            data_frequency = []
            start_index = 0
            for one_of_begin_and_end_pairs in target_begin_and_end_pairs:
                sampling_count = 0

                for n, target_status in enumerate(target_statuses_all[start_index:]):
                    if one_of_begin_and_end_pairs["begin"] <= target_status.created_time and \
                            target_status.created_time < one_of_begin_and_end_pairs["end"] and \
                            target_status.is_closed:
                        # 対象区間内のレコードであればカウント
                        sampling_count += 1
                    elif one_of_begin_and_end_pairs["end"] <= target_status.created_time:
                        # 対象区間から出た時点で抜ける
                        start_index = n
                        break

                data_frequency.append(sampling_count)

            # 出来上がったグラフデータをグラフリストに格納
            graph["data"]["datasets"][0]["data"] = data_frequency
            graphs.append(graph)

        ##### 占有率 (抽出開始時刻よりも前から継続して入室中だったデータはカウント対象に含まれないので注意) #####
        # 系列ごとにグラフデータを分けて作成
        for i, series_toilet in enumerate(grouped_toilets):
            graph = {
              "type": "bar",
              "data": {
                "labels": labels,
                "datasets": [{
                  "label": f"{series_toilet.ToiletGroup.name} - {step_hours}時間あたりの占有率",
                  "data": []
                }]
              }
            }

            # この系列に属するトイレマスターのレコードを抽出
            target_toilets_id_list = [
                x.Toilet.id
                for x in toilets
                if x.ToiletGroupMap.toilet_group_id == series_toilet.ToiletGroupMap.toilet_group_id
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

            data_occupancy = []
            start_index = 0

            # 個室1室あたりが最大占有率になる時間秒数
            max_occupancy_time = step_hours * 60 * 60

            # トイレIDごとに直前に入室した時刻を記憶できるようにしておく
            temp_last_start_times = {
                x: None
                for x in target_toilets_id_list
            }

            # 先頭のサンプリング時間から順に抽出していく
            for m, one_of_begin_and_end_pairs in enumerate(target_begin_and_end_pairs):
                # 抽出対象区間をまたいで占有している場合は現在の抽出開始時刻に合わせておく
                temp_last_start_times = {
                    x: None if temp_last_start_times[x] is None else one_of_begin_and_end_pairs["begin"]
                    for x in target_toilets_id_list
                }

                # 抽出対象区間内における個室ごとの占有時間累計秒数
                occupied_times = {
                    x: 0
                    for x in target_toilets_id_list
                }

                for n, target_status in enumerate(target_statuses_all[start_index:]):
                    if one_of_begin_and_end_pairs["begin"] <= target_status.created_time and \
                            target_status.created_time < one_of_begin_and_end_pairs["end"]:
                        if target_status.is_closed:
                            # 対象区間内の入室記録にヒットしたら占有時間の計算を開始する
                            temp_last_start_times[target_status.toilet_id] = target_status.created_time
                        else:
                            # 対象区間内の退室記録にヒットしたら占有時間の計算を完了する
                            time_delta = target_status.created_time - temp_last_start_times[target_status.toilet_id]
                            occupied_times[target_status.toilet_id] += time_delta.total_seconds()
                            temp_last_start_times[target_status.toilet_id] = None
                    elif one_of_begin_and_end_pairs["end"] <= target_status.created_time:
                        # 抽出対象区間から抜けたらその時間の集計を完了する
                        start_index = n

                        # 抽出対象区間の終端まで入室中だったものはその終端で区切る
                        for id, last_start_time in temp_last_start_times.items():
                            if last_start_time is not None:
                                time_delta = one_of_begin_and_end_pairs["end"] - temp_last_start_times[target_status.toilet_id]
                                occupied_times[target_status.toilet_id] += time_delta.total_seconds()
                                # NOTE: 次の抽出対象区間に回った後にその抽出開始時刻で占有時間の計算を開始する

                        break

                # トイレグループ内の個室ごとの占有時間を理論上のMAX占有時間で割った割合について、トイレグループ内の個室全体で相加平均したものをこのトイレグループの占有率とする
                data_occupancy.append(
                  sum([
                    (occupied_time / max_occupancy_time)
                    for x, occupied_time in occupied_times.items()
                  ]) / len(occupied_times)
                )

            # 出来上がったグラフデータをグラフリストに格納
            graph["data"]["datasets"][0]["data"] = data_occupancy
            graphs.append(graph)

    # API側はデータを返すだけで、見た目やオプションはクライアント側で付加してもらうポリシーとする
    result = {
        "success": True,
        "message": "",
        "graphs": graphs
    }
    logger.info(f"[log] API Response. :success={True} :graphs_length={len(graphs)}")
    return jsonify(result)
