FROM debian:latest

# 依存パッケージのインストール
RUN apt-get update && apt-get install -y \
    apache2 \
    apache2-dev \
    wget \
    ca-certificates \
    make \
    gcc \
    musl-dev \
    build-essential \
    zlib1g-dev \
    libssl-dev \
    libffi-dev \
    sqlite3 \
    libsqlite3-dev \
    libbz2-dev \
    libncurses5-dev \
    libgdbm-dev \
    liblzma-dev \
    libssl-dev \
    tcl-dev \
    tk-dev \
    libreadline-dev \
 && apt-get clean \
 && apt-get autoremove \
 && rm -rf /var/lib/apt/lists/*

# Python のソースインストール
RUN wget -O /tmp/python3.7.tar.gz https://www.python.org/ftp/python/3.7.2/Python-3.7.2.tgz && \
    tar -C /tmp -xvf /tmp/python3.7.tar.gz && \
    rm -f /tmp/python3.7.tar.gz
WORKDIR /tmp/Python-3.7.2
RUN ./configure CFLAGS=-fPIC --enable-optimizations --prefix=/usr/local/python3.7 && \
    make && make install
WORKDIR /tmp
RUN rm -rf /tmp/Python-3.7.2 && \
    ln -s /usr/local/python3.7/lib/libpython3.7.so.1.0 /usr/lib/libpython3.7.so.1.0 && \
    ln -s /usr/local/python3.7/bin/python3.7 /usr/bin/python3 && \
    ln -s /usr/local/python3.7/bin/pip3.7 /usr/bin/pip3 && \
    pip3 install --upgrade pip

# mod_wsgi のソースインストール
RUN wget -O /tmp/mod_wsgi.tar.gz https://github.com/GrahamDumpleton/mod_wsgi/archive/4.5.6.tar.gz && \
    tar -C /tmp -xvf /tmp/mod_wsgi.tar.gz && \
    rm /tmp/mod_wsgi.tar.gz
WORKDIR /tmp/mod_wsgi-4.5.6
RUN ./configure CFLAGS=-fPIC --with-python=/usr/bin/python3 --with-apxs=/usr/bin/apxs && \
    make && make install

# サーバーアプリケーションの依存パッケージのインストール
COPY ./requirements.txt /var/www/apache-flask/requirements.txt
RUN pip3 install -r /var/www/apache-flask/requirements.txt
RUN pip3 freeze
RUN ln -s /usr/local/python3.7/bin/alembic /usr/bin/alembic

# Apache2の mod_wsgi に関する設定ファイルを適用
COPY ./apache-flask.conf /etc/apache2/sites-available/apache-flask.conf
RUN a2ensite apache-flask
RUN a2enmod headers

# WSGI Webアプリケーションをホストから丸ごとコピー
COPY ./apache-flask.wsgi /var/www/apache-flask/apache-flask.wsgi
COPY ./app /var/www/apache-flask/app/
COPY ./migrate /var/www/apache-flask/migrate/
COPY ./model /var/www/apache-flask/model/
COPY ./alembic.ini /var/www/apache-flask/
COPY ./logging.ini /var/www/apache-flask/
RUN mkdir /var/www/apache-flask/db

# Apache2の mod_wsgi に関する設定ファイルを適用
RUN a2dissite 000-default.conf
RUN a2ensite apache-flask.conf

# コンテナー側のポートを開ける
EXPOSE 80

# WSGI Webアプリケーション のディレクトリーに移動
WORKDIR /var/www/apache-flask

# DBマイグレーションを実行、デフォルトのレコードを流し込む
RUN alembic upgrade head && \
    alembic revision --autogenerate && \
    alembic upgrade head && \
    python3 ./model/main.py && \
    chown -R www-data:www-data /var/www/apache-flask/db

# Apache2 をフォアグラウンドで起動
CMD  /usr/sbin/apache2ctl -D FOREGROUND
