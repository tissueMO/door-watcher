############################################################
# From https://github.com/Craicerjack/apache-flask
# Target Python Version is 3.6
# $ docker run -p 81:80 --rm --privileged -d {CONTAINER_NAME}
############################################################
# Set the base image
FROM debian:latest

# File Author / Maintainer
MAINTAINER Carlos Tighe

# Packages
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
 && apt-get clean \
 && apt-get autoremove \
 && rm -rf /var/lib/apt/lists/*

# Installing Python3.8
RUN wget -O /tmp/python3.8.tar.gz https://www.python.org/ftp/python/3.8.0/Python-3.8.0.tgz && \
    tar -C /tmp -xvf /tmp/python3.8.tar.gz && \
    rm -f /tmp/python3.8.tar.gz
WORKDIR /tmp/Python-3.8.0
RUN ./configure CFLAGS=-fPIC --enable-shared --enable-optimizations --prefix=/usr/local/python3.8 && \
    make && make install
WORKDIR /tmp
RUN rm -rf /tmp/Python-3.8.0 && \
    ln -s /usr/local/python3.8/lib/libpython3.8.so.1.0 /usr/lib/libpython3.8.so.1.0 && \
    ln -s /usr/local/python3.8/bin/python3.8 /usr/bin/python3 && \
    ln -s /usr/local/python3.8/bin/pip3.8 /usr/bin/pip3 && \
    pip3 install --upgrade pip

# mod_wsgi compilation
RUN wget -O /tmp/mod_wsgi.tar.gz https://github.com/GrahamDumpleton/mod_wsgi/archive/4.6.5.tar.gz && \
    tar -C /tmp -xvf /tmp/mod_wsgi.tar.gz && \
    rm /tmp/mod_wsgi.tar.gz
WORKDIR /tmp/mod_wsgi-4.6.5

##### 2020.01.12: ここまでできた #####

RUN ./configure CFLAGS=-fPIC --enable-shared --with-python=/usr/bin/python3 --with-apxs=/usr/bin/apxs && \
    make && make install clean

# Copy over and install the requirements
COPY ./app/requirements.txt /var/www/apache-flask/app/requirements.txt
RUN pip3 install -r /var/www/apache-flask/app/requirements.txt

# Copy over the apache configuration file and enable the site
COPY ./apache-flask.conf /etc/apache2/sites-available/apache-flask.conf
RUN a2ensite apache-flask
RUN a2enmod headers

# Copy over the wsgi file
COPY ./apache-flask.wsgi /var/www/apache-flask/apache-flask.wsgi
COPY ./run.py /var/www/apache-flask/run.py
COPY ./app /var/www/apache-flask/app/

RUN a2dissite 000-default.conf
RUN a2ensite apache-flask.conf

EXPOSE 80

WORKDIR /var/www/apache-flask

# CMD ["/bin/bash"]
CMD  /usr/sbin/apache2ctl -D FOREGROUND
# The commands below get apache running but there are issues accessing it online
# The port is only available if you go to another port first
# ENTRYPOINT ["/sbin/init"]
# CMD ["/usr/sbin/apache2ctl"]
