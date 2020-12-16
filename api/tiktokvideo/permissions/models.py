# Create your models here.

from django.db import models
from django.utils.translation import ugettext_lazy as _

"""

基于rbac 设计理念的权限模块设计，这里简化了
关于rabc: https://shuwoom.com/?p=3041

用户组: 权限归类，用户归属于哪个权限组就拥有改权限组的所有权限
基础权限:  系统的基础功能权限，开发级别维护，不对外开放

"""


class UserGroups(models.Model):
    """
    用户组/角色
    """
    title = models.CharField(
        verbose_name=_('用户组名称'),
        max_length=64,
        unique=True
    )
    description = models.CharField(
        verbose_name=_('用户组名称描述'),
        max_length=256,
        null=True,
        blank=True
    )
    feature_modules = models.ManyToManyField(
        verbose_name=_('用户组权限'),
        to='PermissionsBase'
    )
    is_active = models.BooleanField(
        _('是否使用'),
        default=True
    )

    class Meta:
        verbose_name = '用户组'
        verbose_name_plural = verbose_name
        db_table = 'UserGroups'

    def __str__(self):
        return self.title


class PermissionsBase(models.Model):
    """
    基础权限
    """
    MENU, FUNCTIONS = 0, 1

    SOURCE = (
        (MENU, '菜单'),
        (FUNCTIONS, '功能'),
    )
    name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('菜单名称')
    )
    path = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=_("路径名称")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="状态"

    )
    category = models.CharField(
        choices=SOURCE,
        max_length=64,
        default=FUNCTIONS,
        verbose_name='类别'
    )
    pid = models.ForeignKey(
        'self',
        verbose_name=_('父级'),
        related_name='child_feature_modules',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    order_num = models.PositiveSmallIntegerField(
        default=0,
        null=True,
        verbose_name="排序码"
    )

    class Meta:
        verbose_name = '基础权限'
        verbose_name_plural = verbose_name
        unique_together = ("name", "pid",)
        db_table = 'PermissionsBase'
        ordering = ['order_num', ]

    def __str__(self):
        return self.name
