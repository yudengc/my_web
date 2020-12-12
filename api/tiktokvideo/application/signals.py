from datetime import datetime

from django.db.models.signals import post_save, post_init
from django.dispatch import receiver

from application.models import VideoOrder


# @receiver(post_init, sender=VideoOrder)
# def VideoOrder_post_init(instance, **kwargs):
#     instance.__original_status = instance.status
#     # instance.__original_reject_reason = instance.reject_reason
#
#
# @receiver(post_save, sender=VideoOrder, dispatch_uid='order_post_save')
# def VideoOrder_post_save(instance, created, **kwargs):
#     if created:
#         pass
#     else:
#         if instance.__original_status == VideoOrder.
#             pass


@receiver(post_init, sender=VideoOrder)
def video_order_post_init(instance, **kwargs):
    instance.__original_status = instance.status


@receiver(post_save, sender=VideoOrder, dispatch_uid='order_post_save')
def video_order_post_save(instance, created, **kwargs):
    if not created and instance.status != instance.__original_status:
        # 状态修改记录对应时间(不要用save，不然会重复调用signal导致报错)
        status = instance.status
        now = datetime.now()
        o_qs = VideoOrder.objects.filter(id=instance.id)
        if status == VideoOrder.WAIT_COMMIT:
            o_qs.update(send_time=now)
        elif status == VideoOrder.WAIT_RETURN:
            o_qs.update(check_time=now)
        elif status == VideoOrder.DONE:
            o_qs.update(done_time=now)
            if not instance.is_return:
                # 无需返样，后台审核后订单直接为完成
                o_qs.update(check_time=now)
        elif status == VideoOrder.EXCEPTION:
            o_qs.update(close_time=now)
