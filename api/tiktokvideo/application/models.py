from django.db import models

from libs.common.utils import get_application_order
from users.models import BaseModel


class VideoOrder(BaseModel):
    """短视频申请订单"""
    user = models.ForeignKey(
        'users.Users',
        related_name='apply_sample',
        on_delete=models.CASCADE,
        verbose_name='账号'
    )
    demand = models.ForeignKey(
        'demand.VideoNeeded',
        related_name='video_orders',
        on_delete=models.CASCADE,
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
        verbose_name='寄样收货人名字',
        null=True
    )
    receiver_phone = models.CharField(
        verbose_name='寄样收货人电话',
        null=True
    )
    receiver_province = models.CharField(
        verbose_name='寄样所在地省',
        max_length=128,
        null=True
    )
    receiver_city = models.CharField(
        verbose_name='寄样所在地市',
        max_length=128,
        null=True
    )
    receiver_district = models.CharField(
        verbose_name='寄样所在地地区',
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

    kol_remark = models.CharField(
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
    status = models.PositiveSmallIntegerField(
        verbose_name="订单状态",
        default=0,
        choices=(
            (0, '待发货'),
            (1, '待提交'),
            (3, '待验收'),
            (4, '待反样'),
            (5, '已完成'),
            (6, '订单异常'),
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

