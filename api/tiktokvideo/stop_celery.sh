#!/bin/bash
ps -ef | grep celery| grep -w tiktokvideo | grep -v grep | awk '{print $2}' | xargs -i kill -9 {}

