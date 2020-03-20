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
from app.main import app
logger = Common.get_logger("root")


@app.route("/", methods=["GET"])
def status():
    """現在のトイレ在室状況を返します。
    なお、システム停止モードに移行している間はすべて success=False として返します。

    Returns:
        Response -- application/json = {
          success: True or False,
          message: "エラーメッセージ",    // エラー発生時のみ。正常完了時は空文字
          status: [
            {
              name: "4F 男性用トイレ"    // トイレグループの名称
              valid: True or False,    // このトイレグループの状況を取得できたかどうか
              used: 1,                 // このトイレグループにおける現在の使用数
              max: 2,                  // このトイレグループの部屋数
              rate100: 0-100,          // このトイレグループの使用率% (同じ名前のトイレを合算した使用率%)
              details: [               // このトイレグループの仔細
                {
                  name: "4F 男性用トイレ (洋式)",  // このトイレの名称
                  used: True or False,   // このトイレが現在使用中であるかどうか
                  valid: True or False,  // このトイレが現在トラブルが起きていない状態であるかどうか
                },
                ...
              ],
            },
            ...
          ]
        }
    """
    from model.toilet import Toilet
    from model.toilet_group import ToiletGroup
    from model.toilet_group_map import ToiletGroupMap
    logger.info(f"[status] API Called.")

    with Common.create_session() as session:
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

        # トイレグループマスターを取得: トイレへの紐付け情報も合わせて取得
        toilet_groups = session \
            .query(
                ToiletGroup,
                ToiletGroupMap,
                func.count().label("max")
            ) \
            .outerjoin(ToiletGroupMap, ToiletGroup.id == ToiletGroupMap.toilet_group_id) \
            .order_by(asc(ToiletGroup.id)) \
            .group_by(ToiletGroup.id) \
            .all()

        # トイレマスターを取得: トイレグループへの紐付け情報も合わせて取得
        toilets = session \
            .query(
                Toilet,
                ToiletGroupMap,
            ) \
            .outerjoin(ToiletGroupMap, Toilet.id == ToiletGroupMap.toilet_id) \
            .order_by(asc(Toilet.id)) \
            .all()

        # 返却用の形式に変換
        result = {"status": []}
        for i, toilet_group in enumerate(toilet_groups):
            result["status"].append({
                "name": toilet_group.ToiletGroup.name,
                "valid": toilet_group.ToiletGroup.valid,
                "max": toilet_group.max
            })

            result["status"][-1]["used"] = 0
            result["status"][-1]["rate100"] = 0
            result["status"][-1]["details"] = []

            if not toilet_group.ToiletGroup.valid:
                # このトイレグループ全体が無効になっている
                continue
            if toilet_group.max == 0:
                # このトイレグループに紐づくトイレが存在しない
                continue

            # このグループ内の個々のトイレの仔細をデータに加える
            for n, toilet in enumerate(toilets):
                if toilet.ToiletGroupMap.toilet_group_id != toilet_group.ToiletGroup.id:
                    continue
                if toilet.Toilet.is_closed:
                    result["status"][-1]["used"] += 1

                result["status"][-1]["details"].append({
                    "name": toilet.Toilet.name,
                    "used": toilet.Toilet.is_closed,
                    "valid": toilet.Toilet.valid
                })

            result["status"][-1]["rate100"] = \
                int(result["status"][-1]["used"] / toilet_group.max * 100)

    result["success"] = True
    result["message"] = ""
    logger.info(f"[status] API Response. :success={True} :status_length={len(result['status'])}")
    return jsonify(result)
