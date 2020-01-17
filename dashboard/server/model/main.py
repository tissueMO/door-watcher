###############################################################################
#    初期データを流し込みます。
#    マイグレーション実行後に手動で呼び出して下さい。
#    ただし、起動ディレクトリーは /server/ 直下にしておく必要があります。
###############################################################################
import sys
sys.path.insert(0, ".")
from model.toilet import Toilet
from model.toilet_status import ToiletStatus
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
        Toilet(id=11, name="4F男性用トイレ", valid=True, is_closed=False, modified_time=now),
        Toilet(id=21, name="6F男性用トイレ", valid=True, is_closed=False, modified_time=now),
        Toilet(id=31, name="4F女性用トイレ", valid=False, is_closed=False, modified_time=now),
        Toilet(id=32, name="4F女性用トイレ", valid=False, is_closed=False, modified_time=now),
        Toilet(id=41, name="6F女性用トイレ", valid=False, is_closed=False, modified_time=now),
        Toilet(id=42, name="6F女性用トイレ", valid=False, is_closed=False, modified_time=now)
    ])
    # トイレ入退室トランザクションテーブル
    session.add_all([
      ToiletStatus(toilet_id=11, is_closed=False, created_time=now+timedelta(minutes=0)),
      ToiletStatus(toilet_id=11, is_closed=True, created_time=now+timedelta(minutes=13)),
      ToiletStatus(toilet_id=11, is_closed=False, created_time=now+timedelta(minutes=26)),
      ToiletStatus(toilet_id=11, is_closed=False, created_time=now+timedelta(minutes=39)),
      ToiletStatus(toilet_id=11, is_closed=True, created_time=now+timedelta(minutes=52)),
      ToiletStatus(toilet_id=11, is_closed=True, created_time=now+timedelta(minutes=65)),
      ToiletStatus(toilet_id=11, is_closed=True, created_time=now+timedelta(minutes=78)),
      ToiletStatus(toilet_id=11, is_closed=False, created_time=now+timedelta(minutes=91)),
      ToiletStatus(toilet_id=11, is_closed=False, created_time=now+timedelta(minutes=104)),
      ToiletStatus(toilet_id=11, is_closed=True, created_time=now+timedelta(minutes=117)),
      ToiletStatus(toilet_id=11, is_closed=False, created_time=now+timedelta(minutes=130))
    ])
    # 初期状態で挿入しておきたいレコードの定義 ここまで <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # 変更をコミット
    session.commit()
