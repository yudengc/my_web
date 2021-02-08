#!/bin/bash

branch=$1


cd $RUNPATH

if [[ $branch != "" ]];then
  git pull origin $branch
else
  git pull
fi

pip install -r ${ROOTPATH}/api/requirements/base.txt
pip install -r ${ROOTPATH}/api/requirements/dev.txt
python manage.py makemigrations && python manage.py migrate
