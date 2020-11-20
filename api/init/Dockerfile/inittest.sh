#!/usr/bin/env bash
#read -p '该脚本是测试服初始化库的脚本, 请确认是否继续(Y/N):' input

cd /selection/api
rm */migrations/0*
python manage.py makemigrations && python manage.py migrate_schemas --shared

python manage.py shell << EOF
from tenant.models import Client
tenant = Client(domain_url='127.0.0.1',
                schema_name='test',
                name='test',
                paid_until='2020-02-17',
                on_trial=False,
                created_on='2020-02-17',
                frontend_domain_url='127.0.0.1',
                extension_domain_url='127.0.0.1')

tenant.save()
EOF

python manage.py makemigrations && python manage.py migrate_schemas -s test

python manage.py tenant_command shell --schema=test << EOF
from user.models import User
m = User(phone='13073054476', username='超管',sys_role=0)
m.set_password("123456")
m.save()
EOF