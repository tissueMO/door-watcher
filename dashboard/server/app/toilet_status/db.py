###############################################################################
#    トイレの在室ログを表すテーブル定義です。
###############################################################################
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, Text, Boolean
from sqlalchemy import ForeignKey

Base = declarative_base()


"""トイレマスター
"""
class Toilet(Base):
  __tablename__ = "toilet"

  # 固有のID
  id = Column(Integer, primary_key=True, autoincrement=True)

  # トイレの名前
  name = Column(Text, nullable=False)

  # 在室しているかどうかに関わらずトイレ自体が利用可能であるかどうか
  valid = Column(Boolean, nullable=False)


"""トイレ在室トランザクション
"""
class ToiletStatus(Base):
  __tablename__ = "toiletstatus"

  # 固有のID
  id = Column(Integer, primary_key=True, autoincrement=True)

  # トイレID
  toilet_id = Column(Integer, nullable=False)

  # 在室しているかどうかに関わらずトイレ自体が利用可能であるかどうか
  valid = Column(Boolean, nullable=False)
