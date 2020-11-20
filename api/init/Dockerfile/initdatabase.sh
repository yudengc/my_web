#!/usr/bin/env bash

#read -p '该脚本会init所有数据库重新创建, 请确认是否继续(Y/N):' input

if [ "$1" != "Y" ];then
    exit 0
fi

if [ $(whoami) != "postgres" ];then
  su - postgres
fi
pg_ctl -D /data/pgsql/data initdb
cd /data/pgsql/data
pg_ctl start -D /data/pgsql/data -l serverlog

psql -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE datname='selection' AND pid<>pg_backend_pid();
"
psql -c "drop database selection;"
psql -c "create database selection;"

user_exists=$(psql -c "SELECT u.usename FROM pg_catalog.pg_user u  where u.usename='selection';")
username=$(echo ${user_exists}|awk '{print $3}')

if [ "${username}" = "(0" ];then
    psql -c "
create user selection with password 'selection';
grant all privileges on database selection to selection;
"
else
    psql -c "
drop user selection;
create user selection with password 'selection';
grant all privileges on database selection to selection;
"
fi

psql -c "create extension citext;"
exit 0

