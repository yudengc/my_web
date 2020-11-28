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
