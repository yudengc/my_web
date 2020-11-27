from django.db import models

from users.models import BaseModel
from django.utils.translation import ugettext_lazy as _


class CreatorAccount(BaseModel):
    """创作者账户"""
    uid = models.OneToOneField(
        "users.Users",
        to_field='uid',
        on_delete=models.DO_NOTHING,
        related_name='creator_account',
    )
    coin_balance = models.IntegerField(
        _('松子余额'),
        default=0
    )
    coin_freeze = models.IntegerField(
        _('待结算松子'),
        default=0
    )

    class Meta:
        db_table = 'CreatorAccount'
        verbose_name = '创作者账户'
        verbose_name_plural = verbose_name


class CreatorBill(models.Model):
    """创作者每月账单"""
    uid = models.ForeignKey(
        "users.Users",
        to_field='uid',
        on_delete=models.DO_NOTHING,
        related_name='creator_bill',
    )
    total = models.IntegerField(
        _('当月结算松子数量'),
        default=0
    )
    bill_date = models.DateField(
        _('本期账单年月'),
    )
    date_created = models.DateTimeField(
        _('账单记录时间'),
        auto_now_add=True
    )
    date_updated = models.DateTimeField(
        _('更新时间'),
        auto_now=True
    )
    # Todo  记得跟订单关联

    class Meta:
        db_table = 'CreatorBill'
        verbose_name = '创作者每月账单'
        verbose_name_plural = verbose_name
        ordering = ('-date_created', )
