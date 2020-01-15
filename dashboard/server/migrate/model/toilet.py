###############################################################################
#    トイレの在室ログを表すテーブル定義です。
###############################################################################
from . import Base
from .toilet_status import ToiletStatus
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, Text, Boolean


"""トイレマスター
"""
class Toilet(Base):
    __tablename__ = "toilet"

    # 固有のID
    id = Column(Integer, primary_key=True, autoincrement=True)
    ## NOTE: SQLite3では基本的に外部キーが非対応であることが多いため廃止
    # toilet_statuses = relationship("ToiletStatus")

    # トイレの名前
    name = Column(Text, nullable=False)

    # 在室しているかどうかに関わらずトイレ自体が利用可能であるかどうか
    valid = Column(Boolean, nullable=False)
