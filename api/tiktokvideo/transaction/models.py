from ckeditor.fields import RichTextField
from django.db import models
from django.db.models import ImageField
from django.utils.translation import ugettext_lazy as _
from users.models import BaseModel
from libs.common.utils import get_out_trade_no


class OrderInfo(models.Model):
    """订单信息"""

    WAIT, SUCCESS, FAIL, TIMEOUT = range(4)
    PACKAGE = 0
    PAY_STATUS = (
        (WAIT, "等待支付"),
        (SUCCESS, "支付成功"),
        (FAIL, "支付失败, 取消支付"),
        (TIMEOUT, "支付超时"),
    )
    uid = models.ForeignKey(
        "users.Users",
        to_field='uid',
        on_delete=models.DO_NOTHING,
        related_name='user_order',
        verbose_name='账号'
    )
    TRAN_TYPE = (
        (PACKAGE, '购买套餐'),
    )
    tran_type = models.PositiveSmallIntegerField(
        _('购买的类型'),
        choices=TRAN_TYPE,
    )
    amount = models.FloatField(
        _('支付金额'),
    )
    out_trade_no = models.CharField(
        _('订单号'),
        max_length=64,
        default=get_out_trade_no,
        unique=True
    )
    status = models.PositiveSmallIntegerField(
        _('支付状态'),
        choices=PAY_STATUS,
        default=WAIT
    )
    parm_id = models.PositiveSmallIntegerField(
        _('购买的商品对应的id'),
    )
    date_created = models.DateTimeField(
        _('订单生成时间'),
        auto_now_add=True,
    )

    date_payed = models.DateTimeField(
        _('支付时间'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = '订单信息'
        verbose_name_plural = verbose_name
        db_table = 'OrderInfo'
        ordering = ('-date_created',)

    @staticmethod
    def create_order(user, amount, t_type, p_id):
        order = OrderInfo.objects.create(
            uid=user,
            amount=amount,
            tran_type=t_type,
            parm_id=p_id
        )
        return order


# class TransactionDetail(models.Model):
#     KOL, BUS = range(2)
#     ROLE_CHOICE = (
#         (KOL, '达人'),
#         (BUS, '商家')
#     )
#     """交易明细"""
#     uid = models.ForeignKey(
#         "users.Users",
#         to_field='uid',
#         on_delete=models.DO_NOTHING,
#         related_name='user_trans_detail',
#     )
#
#     out_trade_no = models.CharField(
#         verbose_name='订单号',
#         max_length=100,
#         default=get_out_trade_no
#     )
#
#     amount = models.FloatField(
#         verbose_name='交易金额',
#         default=0
#     )
#
#     tran_type = models.CharField(
#         verbose_name='交易类型',
#         max_length=64,
#         null=True,
#         blank=True
#     )
#
#     desc = models.CharField(
#         verbose_name='描述',
#         max_length=64,
#         null=True
#     )
#
#     date_recorded = models.DateTimeField(
#         verbose_name='记录时间',
#         auto_now=True
#     )
#
#     class Meta:
#         verbose_name = "交易明细"
#         verbose_name_plural = verbose_name
#         db_table = 'TransactionDetail'
#         ordering = ('-date_recorded',)
#
#     @staticmethod
#     def record_detail(user, amount, tran_type, desc):
#         TransactionDetail.objects.create(
#             uid=user,
#             amount=amount,
#             tran_type=tran_type,
#             desc=desc,
#         )


# class RechargeConfig(BaseModel):
#     ONE_MONTH, THREE_MONTH, ONE_YEAR = range(1, 4)
#     SERVICE_TIME = (
#         (ONE_MONTH, '一个月'),
#         (THREE_MONTH, '三个月'),
#         (ONE_YEAR, '一年'),
#     )
#     service_time = models.PositiveSmallIntegerField(
#         # 1个月 3个月 1年
#         verbose_name='会员时长',
#         choices=SERVICE_TIME
#     )
#     amount = models.FloatField(
#         verbose_name='金额',
#         default=0
#     )
#     content = models.TextField(
#         verbose_name='会员权益内容',
#         null=True
#     )
#
#     class Meta:
#         verbose_name = "会员充值配置"
#         verbose_name_plural = verbose_name
#         db_table = 'RechargeConfig'


class Package(BaseModel):
    """套餐包"""
    UNPUBLISHED, PUBLISHED = range(2)
    STATUS = (
        (UNPUBLISHED, '未发布'),
        (PUBLISHED, '已发布'),
    )
    status = models.PositiveIntegerField(
        _('套餐状态'),
        choices=STATUS,
        default=UNPUBLISHED
    )
    uid = models.ManyToManyField(
        "users.Users",
        through='UserPackageRelation',
        related_name='user_package',
    )
    package_title = models.CharField(
        _('套餐名称'),
        max_length=512,
    )
    package_amount = models.DecimalField(
        _('套餐包金额'),
        max_digits=18,
        decimal_places=2,
        default=0
    )
    video_num = models.PositiveIntegerField(
        verbose_name='赠送视频数',
        default=0
    )
    package_content = ImageField(
        verbose_name='套餐包内容图片',
        upload_to='package',
        null=True,
        blank=True,
    )
    expiration = models.PositiveIntegerField(
        _('套餐有效天数'),
        default=0
    )

    class Meta:
        db_table = 'Package'
        verbose_name = '商家套餐'
        verbose_name_plural = verbose_name
        ordering = ('-date_created', )


class UserPackageRelation(BaseModel):
    uid = models.ForeignKey(
        "users.Users",
        to_field='uid',
        on_delete=models.DO_NOTHING,
    )
    package = models.ForeignKey(
        "Package",
        on_delete=models.DO_NOTHING,
    )
    expiration_time = models.DateTimeField(
        _('套餐到期时间'),
        null=True
    )
    UNTREATED, PROCESSED = range(2)
    status = models.PositiveSmallIntegerField(
        _('跟进状态'),
        default=UNTREATED,
        choices=(
            (UNTREATED, '待跟进'),
            (PROCESSED, '已跟进'),
        )
    )

    class Meta:
        verbose_name = '套餐购买记录'
        verbose_name_plural = verbose_name
        db_table = 'UserPackageRelation'
        unique_together = ('uid', 'package')
