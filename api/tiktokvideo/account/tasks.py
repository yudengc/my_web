from celery import shared_task
from django.db.models import FloatField, F, Sum

from account.models import CreatorBill
from application.models import VideoOrder
from libs.common.utils import get_last_year_month
from users.models import Users


@shared_task
def task_create_bill():
    """
    每月8号产生上个月创作者账单
    """
    print('===============================开始执行task_create_bill定时任务=====================================')
    create_lis = []
    year, last_month = get_last_year_month()
    creator_qs = Users.objects.filter(identity=Users.CREATOR, sys_role=Users.COMMON)
    print(creator_qs,111111)
    for creator_obj in creator_qs:
        last_month_reward = VideoOrder.objects.filter(user=creator_obj,
                                                      status=VideoOrder.DONE,
                                                      done_time__year=year,
                                                      done_time__month=last_month).aggregate(
            total=Sum(F('num_selected') * F('reward'), output_field=FloatField()))['total']
        if not last_month_reward:
            last_month_reward = 0
        create_lis.append(CreatorBill(uid=creator_obj,
                                      bill_year=year,
                                      bill_month=last_month,
                                      total=last_month_reward))
    print(create_lis, 222222)
    CreatorBill.objects.bulk_create(create_lis, batch_size=600)
    print('===============================task_create_bill定时任务完成======================================')
