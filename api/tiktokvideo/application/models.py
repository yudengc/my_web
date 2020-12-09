from django.contrib.postgres.fields import JSONField
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
    sample_count = models.PositiveIntegerField(
        verbose_name='样品数',
        default=1
    )
    is_return = models.BooleanField(
        verbose_name='是否返样',
        default=False
    )
    reward = models.PositiveIntegerField(
        # 默认使用的是合同上的酬劳，但是后台可改每条订单的可得酬劳
        verbose_name='单条视频的酬劳（松子）',
        default=0
    )
    order_video = models.ManyToManyField(
        # 订单成品视频
        'Video',
        related_name='orders',
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
    WAIT_SEND, WAIT_COMMIT, WAIT_CHECK, WAIT_RETURN, DONE, EXCEPTION = range(6)
    status = models.PositiveSmallIntegerField(
        verbose_name="订单状态",
        default=WAIT_SEND,
        choices=(
            (WAIT_SEND, '待发货'),
            (WAIT_COMMIT, '待提交'),
            (WAIT_CHECK, '待验收'),
            (WAIT_RETURN, '待返样'),
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
    close_time = models.DateTimeField(
        null=True,
        verbose_name='关闭时间（审核不通过时的时间）'
    )

    class Meta:
        verbose_name = '短视频申请订单'
        verbose_name_plural = verbose_name
        db_table = 'VideoOrder'
        ordering = ('-date_created',)


class VideoOrderDetail(models.Model):
    """VideoOrder分表"""
    video_order = models.OneToOneField(
        'VideoOrder',
        related_name='video_order_detail',
        on_delete=models.CASCADE,
    )

    demand_detail = JSONField(
        verbose_name="申请那一刻的需求详情",
        null=True
    )

    # goods desc
    goods_title = models.CharField(
        verbose_name='标题',
        max_length=128,
        blank=True
    )
    goods_link = models.URLField(
        verbose_name='商品链接',
        max_length=3000,
    )
    goods_images = models.URLField(
        verbose_name='商品主图',  # 来自于goods_link解析
        max_length=3000,
    )
    TB, JD, KL, DY = range(4)
    CHANEL = (
        (TB, "淘宝"),
        (JD, "京东"),
        (KL, "网易考拉"),
        (DY, "抖音小店"),
    )
    goods_channel = models.PositiveSmallIntegerField(
        verbose_name='商品来源',
        default=TB,
        choices=CHANEL
    )
    category = models.ForeignKey(
        'config.GoodsCategory',
        on_delete=models.DO_NOTHING,
        related_name='video_order_category',
        null=True
    )

    # 样品接受者（创作者） desc
    receiver_name = models.CharField(
        verbose_name='样品收货人名字',
        max_length=64,
        null=True
    )
    receiver_phone = models.CharField(
        verbose_name='样品收货人电话',
        max_length=64,
        null=True
    )
    # receiver_province = models.CharField(
    #     verbose_name='样品收货人所在地省',
    #     max_length=128,
    #     null=True
    # )
    # receiver_city = models.CharField(
    #     verbose_name='样品收货人所在地市',
    #     max_length=128,
    #     null=True
    # )
    # receiver_district = models.CharField(
    #     verbose_name='样品收货人所在地地区',
    #     max_length=128,
    #     null=True
    # )
    receiver_location = models.CharField(
        verbose_name='样品收货人寄样具体地址(包括省市区)',
        max_length=128,
        null=True,
    )
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

    # 返样接收者（商家） desc
    return_receiver_name = models.CharField(
        verbose_name='返样收货人名字',
        max_length=64,
        null=True
    )
    return_receiver_phone = models.CharField(
        verbose_name='返样收货人电话',
        max_length=64,
        null=True
    )
    # return_receiver_province = models.CharField(
    #     verbose_name='返样收货人所在地省',
    #     max_length=128,
    #     null=True
    # )
    # return_receiver_city = models.CharField(
    #     verbose_name='返样收货人所在地市',
    #     max_length=128,
    #     null=True
    # )
    # return_receiver_district = models.CharField(
    #     verbose_name='返样收货人所在地地区',
    #     max_length=128,
    #     null=True
    # )
    return_receiver_location = models.CharField(
        verbose_name='返样收货人寄样具体地址(包括省市区)',
        max_length=128,
        null=True,
    )
    return_company = models.CharField(
        verbose_name="反样物流公司",
        max_length=128,
        null=True,
        # choices=COMPANY_CHOICES
    )
    return_express = models.CharField(
        verbose_name="反样快递单号",
        max_length=64,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = '短视频申请订单表2'
        verbose_name_plural = verbose_name
        db_table = 'VideoOrderDetail'


class Video(models.Model):
    video_url = models.URLField(
        max_length=1000
    )
    # order = models.ForeignKey(
    #     'VideoOrder',
    #     related_name='order_video',
    #     on_delete=models.CASCADE
    # )
    date_created = models.DateTimeField(
        verbose_name='创建时间',
        auto_now_add=True
    )

    class Meta:
        verbose_name = '视频成品'
        verbose_name_plural = verbose_name
        db_table = 'Video'
        ordering = ('-date_created',)

    def __str__(self):
        return self.video_url
