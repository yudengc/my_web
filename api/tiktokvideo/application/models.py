from django.db import models

from libs.common.utils import get_application_order
from users.models import BaseModel


class VideoOrder(BaseModel):
    """短视频申请订单"""
    user = models.ForeignKey(
        'users.Users',
        to_field='uid',
        related_name='apply_sample',
        on_delete=models.CASCADE,
        verbose_name='账号'
    )
    demand = models.ForeignKey(
        'demand.VideoNeeded',
        related_name='video_orders',
        on_delete=models.CASCADE,
        db_index=True
    )
    order_number = models.CharField(
        verbose_name="订单号",
        unique=True,
        default=get_application_order,
        max_length=128,
    )
    num_selected = models.PositiveIntegerField(
        verbose_name='选择拍摄视频数',
        default=0
    )
    video = models.URLField(
        verbose_name="拍摄视频url",
        max_length=1000,
        null=True,
        blank=True
    )

    # receiver desc
    receiver_name = models.CharField(
        verbose_name='收货人名字',
        max_length=64,
        null=True
    )
    receiver_phone = models.CharField(
        verbose_name='收货人电话',
        max_length=64,
        null=True
    )
    receiver_province = models.CharField(
        verbose_name='所在地省',
        max_length=128,
        null=True
    )
    receiver_city = models.CharField(
        verbose_name='所在地市',
        max_length=128,
        null=True
    )
    receiver_district = models.CharField(
        verbose_name='所在地地区',
        max_length=128,
        null=True
    )
    receiver_location = models.CharField(
        verbose_name='寄样具体地址',
        max_length=128,
    )

    # logistics desc
    company = models.CharField(
        verbose_name="物流公司",
        max_length=128,
        null=True,
        # choices=COMPANY_CHOICES
    )

    express = models.CharField(
        verbose_name="快递单号",
        max_length=64,
        null=True,
        blank=True,
    )

    # remark
    reject_reason = models.CharField(
        verbose_name="拒绝理由",
        max_length=1024,
        null=True,
        blank=True
    )

    remark = models.CharField(
        verbose_name="工作人员备注(异常备注)",
        max_length=1024,
        null=True,
        blank=True
    )

    creator_remark = models.CharField(
        verbose_name="创作者备注",
        max_length=1024,
        null=True,
        blank=True
    )

    system_remark = models.CharField(
        verbose_name="系统备注",
        max_length=1024,
        null=True
    )

    # status
    WAIT_SEND, WAIT_COMMIT, WAIT_CHECK, WAIT_RETURN, DONE, EXCEPTION = range(7)
    status = models.PositiveSmallIntegerField(
        verbose_name="订单状态",
        default=WAIT_SEND,
        choices=(
            (WAIT_SEND, '待发货'),
            (WAIT_COMMIT, '待提交'),
            (WAIT_CHECK, '待验收'),
            (WAIT_RETURN, '待反样'),
            (DONE, '已完成'),
            (EXCEPTION, '订单异常'),
        ),
    )

    # time desc
    check_time = models.DateTimeField(
        null=True,
        verbose_name='审核时间'
    )
    send_time = models.DateTimeField(
        null=True,
        verbose_name='发货时间'
    )
    done_time = models.DateTimeField(
        null=True,
        verbose_name='订单完成时间'
    )

    class Meta:
        verbose_name = '短视频申请订单'
        verbose_name_plural = verbose_name
        db_table = 'VideoOrder'

