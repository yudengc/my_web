
FROM python:3.6.10-alpine3.11

ARG RUNPATH="/tiktokvideo"
ENV RUNPATH=$RUNPATH

RUN echo -e "http://mirrors.aliyun.com/alpine/v3.11/main\nhttp://mirrors.aliyun.com/alpine/v3.11/community" > /etc/apk/repositories
RUN apk update && apk add --no-cache nginx git build-base openldap-dev supervisor redis bash postgresql postgresql-dev && mkdir -p /data/pgsql/data \
    && mkdir -p /run/postgresql && chown -R postgres:postgres /run/postgresql && chown -R postgres:postgres /data/pgsql/data
RUN apk add --no-cache --virtual .build-deps  openssl-dev gcc musl-dev python3-dev libffi-dev openssh-client make openrc\
    && mkdir /etc/supervisor.d


RUN git clone http://yudengc:123456@git.darentui.com:3000/lorcyu/tiktokvideo.git -b dengyu-dev --depth=1 $RUNPATH \
    && cd $RUNPATH && git pull && mkdir $RUNPATH/logs/

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/  && pip install --upgrade pip && pip install --no-cache-dir -r $RUNPATH/api/requirements/base.txt \
    && pip install --no-cache-dir gunicorn && pip install --no-cache-dir -r $RUNPATH/api/requirements/dev.txt\
    && apk del .build-deps && mv /usr/local/lib/python3.6/site-packages/crypto /usr/local/lib/python3.6/site-packages/Crypto

ADD tiktokvideo.ini /etc/supervisor.d/tiktokvideo.ini
ADD default.conf /etc/nginx/conf.d/default.conf
ADD entrypoint.sh /entrypoint.sh
ADD .env $RUNPATH/api/.env
ADD initdatabase.sh /initdatabase.sh
ADD inittest.sh /inittest.sh
ADD init_model /usr/local/bin/init_model

RUN sed -i "s/\r//g" /inittest.sh && sed -i "s/\r//g" /initdatabase.sh && sed -i "s/\r//g" /entrypoint.sh \
    && su - postgres -c "bash /initdatabase.sh Y"
#RUN bash /inittest.sh Y && rm /initdatabase.sh /inittest.sh


ENTRYPOINT ["sh", "/entrypoint.sh"]
