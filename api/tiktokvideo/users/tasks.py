from datetime import datetime, timedelta

from celery import shared_task
from django.db.models import Sum, F

from application.models import VideoOrder
from demand.models import VideoNeeded
from transaction.models import UserPackageRecord
from users.models import Users, BusStatistical


@shared_task
def task_save_bus_video_data():
    """商家交付数据周统计(凌晨12点统计前一天数据，保留30条)"""
    today = datetime.today().date()
    bus_user_qs = Users.objects.filter(identity=Users.BUSINESS, sys_role=Users.COMMON, is_superuser=False)
    video_total = 0
    done_total = 0
    pending_total = 0
    for obj in bus_user_qs:
        record_qs = UserPackageRecord.objects.filter(uid=obj)

        # 商家总视频数（商家购买套餐后，套餐内拍摄视频数总和）
        total = record_qs.aggregate(total=Sum(F('buy_video_num') + F('video_num')))['total']
        if not total:
            total = 0

        # 已完成视频数（商家发布的需求订单，订单状态为已完成的视频数总和）
        done_num = VideoOrder.objects.filter(status=VideoOrder.DONE,
                                             demand__uid=obj).aggregate(total=Sum('num_selected'))['total']
        if not done_num:
            done_num = 0

        # 进行中的视频数（需求订单拍摄视频数-已完成订单视频数）
        need_video_num = VideoNeeded.objects.filter(uid=obj).aggregate(total=Sum('video_num_needed'))['total']
        if not need_video_num:
            need_video_num = 0
        ongoing_video_num = need_video_num - done_num

        # 待交付视频数（商家总拍摄视频数-商家发布的需求拍摄视频数）
        pending_video_num = total - need_video_num

        video_total += total
        done_total += done_num
        pending_total += pending_video_num

    bus_statistical_qs = BusStatistical.objects.order_by('date_created')
    if bus_statistical_qs.count() > 30:
        bus_statistical_qs.first().delete()
    BusStatistical.objects.create(total_video=video_total,
                                  done_video=done_total,
                                  pending_video=pending_total,
                                  date=today - timedelta(days=1))
