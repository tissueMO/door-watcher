###############################################################################
#    トイレに対するグループの紐付けを表すテーブルの定義
###############################################################################
from model import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, Text, Boolean, DateTime


"""トイレグループ紐付け用マスター
"""
class ToiletGroupMap(Base):
    __tablename__ = "toilet_group_map"
    __table_args__ = {"extend_existing": True}

    # 固有のID
    id = Column(Integer, primary_key=True, autoincrement=True)

    # トイレID
    toilet_id = Column(Integer, ForeignKey("toilet.id"), nullable=False)

    # トイレグループID
    toilet_group_id = Column(Integer, ForeignKey("toilet_group.id"), nullable=False)
