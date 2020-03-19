###############################################################################
#    トイレの在室ログを表すテーブルの定義
###############################################################################
from model import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, Text, Boolean, DateTime


"""トイレ入退室トランザクションテーブル
"""
class ToiletStatus(Base):
    __tablename__ = "toilet_status"
    __table_args__ = {"extend_existing": True}

    # 固有のID
    id = Column(Integer, primary_key=True, autoincrement=True)

    # トイレID
    toilet_id = Column(Integer, ForeignKey("toilet.id"), nullable=False)

    # トイレのドアが閉まっている (=在室中) かどうか
    is_closed = Column(Boolean, nullable=False)

    # レコード作成日時
    created_time = Column(DateTime, nullable=False)
