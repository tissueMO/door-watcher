###############################################################################
#    アプリケーション自体の状態を示すテーブルの定義
###############################################################################
from . import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, Text, Boolean, DateTime


"""アプリケーション状態マスター
"""
class AppState(Base):
    __tablename__ = "app_state"

    # 固有のID
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 設定名
    name = Column(Text, nullable=True)

    # 状態コード
    state = Column(Integer, nullable=False)

    # 状態説明文
    comment = Column(Text, nullable=True)

    # レコード更新日時
    modified_time = Column(DateTime, nullable=False)
