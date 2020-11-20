#!/usr/bin/env bash

mode=$1
shift

HelpTips="

"

runpath="$RUNPATH/api/tools/manage"

if [ ! -d $runpath ];then
    echo "运行路径不存在："
    echo "检查：$runpath"
    exit 1
fi

script_name=$(ls $runpath/|grep -E "\.sh$"|awk -F'.' '{print $1}')
if [[ $script_name == "" ]];then
    echo "没有找到脚本哦："
    echo "检查：$runpath"
fi

flag=0
for i in $script_name;do
    if [[ $i == $mode ]]; then
        bash $runpath/$i.sh $@
        flag=1
        break
    fi
done


if [ $flag -eq 0 ];then
    echo "只接受这些mode:"
    echo "${script_name}"
fi
