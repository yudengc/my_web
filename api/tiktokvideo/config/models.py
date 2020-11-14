from django.db import models
from django.utils.translation import ugettext_lazy as _

from users.models import BaseModel


class CustomerService(BaseModel):
    """
    客服联系
    """
    desc = models.CharField(
        _("客服描述"),
        max_length=200,
        null=True,
    )
    name = models.CharField(
        _("客服名称"),
        max_length=100,
        null=True,
    )
    weChat_num = models.CharField(
        _("微信号"),
        max_length=100,
        null=True,
    )
    qr_code = models.URLField(
        _("微信二维码"),
        max_length=1000,
        null=True,
    )
    avatar = models.URLField(
        _("客服头像"),
        max_length=1000,
        null=True,
    )

    class Meta:
        verbose_name = "客服联系"
        verbose_name_plural = verbose_name
        db_table = 'CustomerService'
