#!/bin/bash

cd $RUNPATH

exec gunicorn -b 127.0.0.1:9001 -w 2 --threads 8 --access-logfile - tiktokvideo.wsgi
