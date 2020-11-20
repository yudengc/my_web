import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from safedelete.models import SafeDeleteModel

from libs.common.utils import get_iCode


class BaseModel(models.Model):
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
        _('用户账号'),
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
        _('用户状态'),
        choices=STATUS,
        default=APPROVED
    )
    reason = models.CharField(
        _('冻结原因'),
        max_length=100,
        blank=True,
        null=True
    )

    ADMIN, MANAGER, COMMON = range(3)
    sys_role = models.PositiveSmallIntegerField(
        verbose_name="系统身份",
        default=COMMON
    )

    SALESMAN, BUSINESS = range(2)
    IDENTITY = (
        (SALESMAN, '业务员'),
        (BUSINESS, '商家'),
    )
    identity = models.PositiveIntegerField(
        _('用户身份'),
        choices=IDENTITY,
        default=BUSINESS
    )
    salesman_name = models.CharField(
        # 为业务员时才有该字段
        _('业务员名称'),
        max_length=100,
        null=True,
        blank=True,
    )
    iCode = models.CharField(
        _('注册码'),
        max_length=100,
        unique=True,  # 改成跟id有映射关系的了，不要乱改邀请码
    )
    team = models.ForeignKey(
        # 所属团队
        "users.Team",
        on_delete=models.DO_NOTHING,
        related_name='team_user',
        null=True,
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
        verbose_name = '用户管理'
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
        _('用户昵称'),
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


class UserBusiness(BaseModel):
    """
    商家信息
    """
    uid = models.OneToOneField(
        "Users",
        to_field='uid',
        on_delete=models.DO_NOTHING,
        related_name='user_business',
    )
    bus_name = models.CharField(
        _('商家名称'),
        max_length=100,
        null=True,
    )
    name_abb = models.CharField(
        _('商家简称'),
        max_length=10,
        null=True
    )
    contact = models.CharField(
        _('联系人'),
        max_length=10,
        null=True,
    )
    industry = models.CharField(
        _('所属行业'),
        max_length=50,
        null=True,
    )
    category = models.CharField(
        _('商品品类'),
        max_length=50,
        null=True,
    )
    desc = models.TextField(
        _('详细说明'),
        null=True,
    )

    class Meta:
        verbose_name = '商家信息'
        verbose_name_plural = verbose_name
        db_table = 'UserBusiness'


class Team(BaseModel):
    pass
    """
    团队
    """
    leader = models.OneToOneField(
        "Users",
        to_field='uid',
        on_delete=models.DO_NOTHING,
        related_name='user_team',
        null=True,
        unique=True,
        verbose_name='团队主管'
    )
    name = models.CharField(
        _('团队名称'),
        max_length=100,
        null=True
    )
    # number = models.PositiveSmallIntegerField(
    #     _('团队人数'),
    #     default=1,
    # )

    class Meta:
        verbose_name = '团队信息'
        verbose_name_plural = verbose_name
        db_table = 'Team'

    def edit_audit_button(self):
        # 自定义admin按钮
        btn_str = '<a class="btn btn-xs btn-warning" href="{}">' \
                  '<input name="团队成员"' \
                  'type="button" id="passButton" ' \
                  'title="passButton" value="团队成员" class="el-button el-button--primary">' \
                  '</a >'
        return format_html(btn_str, f'/admin/users/teamusers/?team__name={self.name}')

    edit_audit_button.short_description = "操作"

