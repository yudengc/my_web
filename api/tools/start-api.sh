#!/bin/bash
# Copyright: (c) OpenSpug Organization. https://github.com/openspug/spug
# Copyright: (c) <spug.dev@gmail.com>
# Released under the AGPL-3.0 License.
# start api service

cd "$(dirname $(dirname $(readlink -f $0)))/api"

exec gunicorn -b 127.0.0.1:9001 -w 2 --threads 8 --access-logfile - selection.wsgi
