###############################################################################
#    トイレのグループを表すテーブルの定義
###############################################################################
from model import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, Text, Boolean, DateTime


"""トイレグループマスター
"""
class ToiletGroup(Base):
    __tablename__ = "toilet_group"
    __table_args__ = {"extend_existing": True}

    # 固有のID
    id = Column(Integer, primary_key=True, autoincrement=True)

    # トイレのグループ名
    name = Column(Text, nullable=False)

    # トイレグループ全体がサービス上で利用可能であるかどうか
    valid = Column(Boolean, nullable=False)

    # レコード作成日時
    modified_time = Column(DateTime, nullable=False)
