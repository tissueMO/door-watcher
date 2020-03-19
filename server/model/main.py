###############################################################################
#    初期データを流し込みます。
#    マイグレーション実行後に手動で呼び出して下さい。
#    ただし、起動ディレクトリーは /server/ 直下にしておく必要があります。
###############################################################################
import sys
sys.path.insert(0, ".")
from model.toilet import Toilet
from model.toilet_status import ToiletStatus
from model.toilet_group import ToiletGroup
from model.toilet_group_map import ToiletGroupMap
from model.app_state import AppState
from datetime import datetime as dt
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if __name__ == "__main__":
    # セッション作成
    engine = create_engine("sqlite:///db/toilet.db")
    session = sessionmaker(bind=engine)()

    # テーブル内レコード全削除
    session.query(Toilet).delete()
    session.query(ToiletStatus).delete()
    session.query(ToiletGroup).delete()
    session.query(ToiletGroupMap).delete()
    session.query(AppState).delete()

    # 初期状態で挿入するレコードの定義 ここから >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    now = dt.now()

    # アプリケーション状態マスター
    session.add_all([
        AppState(
            id=1, name="システムモード", state=1,
            comment="0=使用できない状態, 1=使用可能な状態",
            modified_time=now
        )
    ])

    # トイレマスター
    session.add_all([
        Toilet(id=11, name="4F 男性用トイレ (洋式)", valid=False, is_closed=False, modified_time=now),
        Toilet(id=21, name="6F 男性用トイレ (洋式)", valid=True, is_closed=False, modified_time=now),
        Toilet(id=31, name="4F 女性用トイレ (和式)", valid=False, is_closed=False, modified_time=now),
        Toilet(id=32, name="4F 女性用トイレ (洋式)", valid=False, is_closed=False, modified_time=now),
        Toilet(id=41, name="6F 女性用トイレ (和式)", valid=False, is_closed=False, modified_time=now),
        Toilet(id=42, name="6F 女性用トイレ (洋式)", valid=False, is_closed=False, modified_time=now)
    ])

    # トイレグループマスター
    session.add_all([
        ToiletGroup(id=10, name="4F 男性用トイレ", valid=False, modified_time=now),
        ToiletGroup(id=20, name="6F 男性用トイレ", valid=True, modified_time=now),
        ToiletGroup(id=30, name="4F 女性用トイレ", valid=False, modified_time=now),
        ToiletGroup(id=40, name="6F 女性用トイレ", valid=False, modified_time=now)
    ])

    # トイレグループマップ
    session.add_all([
        ToiletGroupMap(id=11, toilet_id=11, toilet_group_id=10),
        ToiletGroupMap(id=21, toilet_id=21, toilet_group_id=20),
        ToiletGroupMap(id=31, toilet_id=31, toilet_group_id=30),
        ToiletGroupMap(id=32, toilet_id=32, toilet_group_id=30),
        ToiletGroupMap(id=41, toilet_id=41, toilet_group_id=40),
        ToiletGroupMap(id=42, toilet_id=42, toilet_group_id=40),
    ])

    # # [テスト用] トイレ入退室トランザクションテーブル
    # import random
    # for toilet_id in [11, 21, 31, 32, 41, 42]:
    #     count = random.randint(1, 100)
    #     for i in range(count):
    #         timedelta_minutes = random.randint(1, 10000)
    #         session.add(ToiletStatus(toilet_id=toilet_id, is_closed=True, created_time=now-timedelta(minutes=timedelta_minutes)))
    # 初期状態で挿入しておきたいレコードの定義 ここまで <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # 変更をコミット
    session.commit()
