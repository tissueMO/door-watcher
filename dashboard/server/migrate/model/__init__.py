###############################################################################
#    マイグレーションやORマッピングに使用する共有用メタクラスを生成します。
###############################################################################
from sqlalchemy.ext.declarative.api import declarative_base
Base = declarative_base()


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    engine = create_engine("sqlite:///../../db/toilet.db")

    with engine.connect() as connect:
        # 初期状態で挿入しておきたいレコードを挿入

        # トイレマスター
        connect.execute(f"INSERT INTO toilet (id, name, valid, room_count) VALUES " +
                        f"(1, '4F男性用トイレ', 1, 1)")
        connect.execute(f"INSERT INTO toilet (id, name, valid, room_count) VALUES " +
                        f"(2, '6F男性用トイレ', 1, 1)")
        connect.execute(f"INSERT INTO toilet (id, name, valid, room_count) VALUES " +
                        f"(3, '4F女性用トイレ', 1, 2)")
        connect.execute(f"INSERT INTO toilet (id, name, valid, room_count) VALUES " +
                        f"(4, '6F女性用トイレ', 1, 2)")

        # アプリケーション状態マスター
        connect.execute(f"INSERT INTO app_state (id, name, state, comment, modified_time) VALUES "
                        f"(1, '緊急停止モード', 0, 'すべて使用できない状態にします', '2020-01-01 00:00:00')")
else:
    # このパッケージで定義されているモデルをすべてロード
    # Alembicにて自動的にマイグレーションを行う
    from migrate.model import (toilet, toilet_status, app_state)
