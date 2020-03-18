###############################################################################
#    トイレの在室ログを表すテーブルの定義
###############################################################################
from model import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, Text, Boolean, DateTime


"""トイレマスター
"""
class Toilet(Base):
    __tablename__ = "toilet"
    __table_args__ = {"extend_existing": True}

    # 固有のID
    id = Column(Integer, primary_key=True, autoincrement=True)

    # トイレの名前
    name = Column(Text, nullable=False)

    # 在室しているかどうかに関わらずトイレ自体が利用可能であるかどうか
    valid = Column(Boolean, nullable=False)

    # 在室しているかどうか
    is_closed = Column(Boolean, nullable=False)

    # レコード更新日時
    modified_time = Column(DateTime, nullable=False)
