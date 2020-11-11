import uuid

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import ugettext_lazy as _
from safedelete.models import SafeDeleteModel

from libs.common.utils import get_iCode


class BaseModel(SafeDeleteModel):
    date_created = models.DateTimeField(
        _('创建时间'),
        auto_now_add=True
    )

    date_updated = models.DateTimeField(
        _('更新时间'),
        auto_now=True
    )

    class Meta:
        abstract = True
        ordering = ('-date_created',)


class Users(AbstractUser):
    """
    用户表
    """
    uid = models.UUIDField(
        _('用户ID'),
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    password = models.CharField(
        _('密码'),
        max_length=128,
        null=True,
    )
    username = models.CharField(
        _('用户名'),
        max_length=100,
        unique=True,
    )

    openid = models.CharField(
        _("微信openid"),
        max_length=128,
        null=True
    )

    APPROVED, FROZEN = range(2)
    STATUS = (
        (APPROVED, '正常'),
        (FROZEN, '冻结'),
    )
    status = models.PositiveIntegerField(
        _('账户状态'),
        choices=STATUS,
        default=APPROVED
    )
    reason = models.CharField(
        _('冻结原因'),
        max_length=100,
        null=True
    )

    KOL, BUSINESS, NONE = range(3)
    IDENTITY = (
        (KOL, 'kol'),
        (BUSINESS, 'business'),
        (NONE, 'none'),
    )
    identity = models.PositiveIntegerField(
        _('用户身份'),
        choices=IDENTITY,
        default=NONE
    )

    iCode = models.CharField(
        _('注册码'),
        max_length=100,
        default=get_iCode,
        unique=True,

    )
    date_created = models.DateTimeField(
        _('注册时间'),
        auto_now_add=True
    )
    date_updated = models.DateTimeField(
        _('更新时间'),
        auto_now=True
    )
    USERNAME_FIELD = 'username'

    class Meta:
        db_table = 'Users'
        verbose_name = '用户表'
        verbose_name_plural = verbose_name
        unique_together = (
            ('username', 'uid',),
        )

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self._password = raw_password


class UserBase(BaseModel):
    """
    用户基础信息表
    """

    uid = models.OneToOneField(
        "Users",
        to_field='uid',
        on_delete=models.DO_NOTHING,
        related_name='auth_base',
    )

    nickname = models.CharField(
        _('昵称'),
        max_length=128,
        null=True,
        blank=True,
    )

    phone = models.CharField(
        _('手机号码'),
        max_length=200,
        null=True
    )

    MALE, FEMALE = range(2)

    GENDER = (
        (MALE, '男'),
        (FEMALE, '女'),
    )

    gender = models.PositiveSmallIntegerField(
        _('性别'),
        choices=GENDER,
        default=MALE
    )

    birthday = models.DateField(
        _('出生年月'),
        null=True,
        blank=True,
    )

    email = models.EmailField(
        _('邮箱'),
        null=True,
        blank=True
    )

    avatars = models.URLField(
        _('头像'),
        null=True,
        blank=True,
        max_length=1000,
    )

    class Meta:
        verbose_name = '用户基础信息'
        verbose_name_plural = verbose_name
        db_table = 'UserBase'
        unique_together = ('phone',)

    def __str__(self):
        return self.nickname if self.nickname else ''


class UserExtra(BaseModel):
    """
    用户扩展信息表
    """
    uid = models.OneToOneField(
        "Users",
        to_field='uid',
        on_delete=models.DO_NOTHING,
        related_name='user_extra',
    )

    is_blacklist = models.BooleanField(
        _('是否在黑名单'),
        default=False
    )

    is_vip = models.BooleanField(
        _('是否开通vip'),
        default=False
    )

    member_expiration_time = models.DateTimeField(
        _('会员到期时间'),
        null=True
    )

    class Meta:
        verbose_name = '用户扩展信息表'
        verbose_name_plural = verbose_name
        db_table = 'UserExtra'
