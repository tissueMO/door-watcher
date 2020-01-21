###############################################################################
#    任意の処理を実行するAPIを定義します。
###############################################################################
from datetime import datetime as dt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import Session
from sqlalchemy.pool import SingletonThreadPool
import sys
sys.path.insert(0, ".")

### ロギング設定ロード
import logging
from logging import config
config.fileConfig("./logging.ini")

### 設定値ロード
import configparser
config = configparser.ConfigParser()
config.read("./alembic.ini", "UTF-8")

# DB接続文字列
DB_PATH = config.get("alembic", "sqlalchemy.url")
print(DB_PATH)

### 定数定義
# APIパラメーター日時フォーマット文字列
PARAM_DATETIME_FORMAT = "%Y%m%d"
# システムモードを表すアプリケーション状態マスター上のID
SYSTEM_MODE_APP_STATE_ID = 1
# システムモード [停止] を表すステート値
SYSTEM_MODE_STOP = 0
# システムモード [再開] を表すステート値
SYSTEM_MODE_RUNNING = 1


class SessionFactory(object):
    """DB接続セッションを生成するファクトリークラスです。
    """

    def __init__(self, echo=False):
        self.engine = create_engine(DB_PATH, echo=echo, poolclass=SingletonThreadPool)

    def create(self) -> Session:
        Session = sessionmaker(bind=self.engine)
        return Session()


class SessionContext(object):
    """with構文 に対応させたDB接続セッション管理クラスです。
    """

    def __init__(self, session):
        self.session = session

    def __enter__(self) -> Session:
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        # with構文 を抜けるタイミングで自動的にコミット&クローズ
        self.session.flush()
        self.session.commit()
        self.session.close()


class SessionContextFactory(object):
    """with構文 に対応したDB接続セッションを生成するファクトリークラスです。
    """

    def __init__(self, echo=False):
        self.session_factory = SessionFactory(echo=echo)

    def create(self) -> SessionContext:
        return SessionContext(self.session_factory.create())


def create_session() -> SessionContext:
    """DB接続セッションを作成します。
    この関数の戻り値を受け取る呼出元変数は with構文 を用いて自動クローズの対象とすることを推奨します。

    Returns:
        Session -- DB接続セッション
    """
    return SessionContextFactory(echo=True).create()


def get_system_mode(session: Session) -> int:
    """現在のシステムモードをアプリケーション状態マスターから取得します。

    Arguments:
        session {Session} -- DB接続セッション

    Returns:
        int -- システムモード (SYSTEM_MODE_STOP=停止, SYSTEM_MODE_RUNNING=稼働), マスターデータを取得できなかった場合はNone
    """
    from model.app_state import AppState
    logger = get_logger(__name__)

    try:
        return session \
            .query(AppState.state) \
            .filter(AppState.id == SYSTEM_MODE_APP_STATE_ID) \
            .one() \
            .state
    except NoResultFound:
        logger.error("Method Error. [get_system_mode] アプリケーション状態マスター id={1} のレコードが設定されていません")
        return None


def get_logger(name: str) -> logging.Logger:
    """指定したモジュール名でロガーオブジェクトを生成します。

    Arguments:
        name {str} -- モジュール名

    Returns:
        Logger -- ロガーオブジェクト
    """
    return logging.getLogger(name)
