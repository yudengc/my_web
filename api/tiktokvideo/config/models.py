from django.db import models
from django.db.models import ImageField
from django.utils.translation import ugettext_lazy as _

from users.models import BaseModel


class CustomerService(BaseModel):
    """
    客服联系
    """
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
    # qr_code = models.URLField(
    #     _("微信二维码"),
    #     max_length=1000,
    #     null=True,
    # )
    qr_code = ImageField(
        _("微信二维码"),
        upload_to='config/customer',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "客服联系"
        verbose_name_plural = verbose_name
        db_table = 'CustomerService'


class GoodsCategory(BaseModel):
    """
    商品品类
    """
    title = models.CharField(
        max_length=100
    )

    class Meta:
        verbose_name = '商品品类'
        verbose_name_plural = verbose_name
        db_table = 'GoodsCategory'
