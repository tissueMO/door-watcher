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

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # セッション作成
    engine = create_engine("sqlite:///db/toilet.db")
    session = sessionmaker(bind=engine)()

    # テーブル内レコード全削除
    session.query(Toilet).delete()
    session.query(ToiletStatus).delete()
    session.query(AppState).delete()

    # 初期状態で挿入しておきたいレコードの定義 ここから >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # トイレマスター
    session.add_all([
        Toilet(id=1, name="4F男性用トイレ", valid=True, room_count=1),
        Toilet(id=2, name="6F男性用トイレ", valid=True, room_count=1),
        Toilet(id=3, name="4F女性用トイレ", valid=True, room_count=2),
        Toilet(id=4, name="6F女性用トイレ", valid=True, room_count=2)
    ])
    # アプリケーション状態マスター
    session.add_all([
        AppState(
            id=1, name="システム緊急停止モード", state=0,
            comment="0=使用可能な状態, 1=使用できない状態",
            modified_time=dt.strptime("2020-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        )
    ])
    # 初期状態で挿入しておきたいレコードの定義 ここまで <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # 変更をコミット
    session.commit()
