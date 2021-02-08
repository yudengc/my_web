#!/bin/bash

HelpTips='
readenv 查看当前env配置
$arg="你需要的配置"
如:
manage config readenv
manage config setenv DATABASE_NAME="tiktokvideo"
'

if [ $1 == "readenv" ];then
    cat $RUNPATH/.env
elif [ $1 != 'setenv' ];then
    echo "$HelpTips"
    exit 1
fi

shift

env_file=$RUNPATH/.env

for i in "$@";do
    arg=`echo $i|awk -F'=' '{print $1}'`
    value=`echo $i|awk -F'=' '{print $2}'`
    line_no=$(cat -n $env_file|grep -E "[ \t]*$arg[ \t]*="|awk '{print $1}')
    if [  ];then
    fi
done
