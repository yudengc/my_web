#!/usr/bin/env bash
#read -p '该脚本是测试服初始化库的脚本, 请确认是否继续(Y/N):' input

set -e

cd $RUNPATH

record_path=$ROOTPATH/.init_record

mkdir -p $record_path

schemas_name=$1

if [[ $schemas_name == "" ]];then
    echo "请输入schemas"
    exit 1
fi

done_flag=$record_path/$schemas_name.init

redo=$2

if [[ -f done_flag ]];then
    if [[ $redo != "redo" ]];then
        echo "$schemas_name 已经初始化过了，重新初始化执行 init $schemas_name redo"
        exit 1
    fi
fi

# rm */migrations/0*
python manage.py makemigrations && python manage.py migrate_schemas --shared

python manage.py shell << EOF
from tenant.models import Client
tenant = Client(domain_url='127.0.0.1',
                schema_name='"${schemas_name}"',
                name='"${schemas_name}"',
                paid_until='2020-02-17',
                on_trial=False,
                created_on='2020-02-17',
                frontend_domain_url='127.0.0.1',
                extension_domain_url='127.0.0.1')

tenant.save()
EOF

python manage.py makemigrations && python manage.py migrate_schemas -s ${schemas_name}

python manage.py tenant_command shell --schema=test << EOF
from user.models import User
from user.services import InviteCls
m = User(username='admin',sys_role=0)
m.set_password("123456")
m.save()
m.iCode = InviteCls.encode_invite_code(m.id)
m.save()
EOF

touch $done_flag

