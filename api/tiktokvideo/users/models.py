import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _


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

    pub_openid = models.CharField(
        _("松鼠营销(公众号)openid"),
        max_length=128,
        null=True
    )

    union_id = models.CharField(
        _("松鼠体系的unionid"),
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
    SUPER_ADMIN, ADMIN, COMMON = range(3)
    sys_role = models.PositiveSmallIntegerField(
        verbose_name="系统身份",
        default=COMMON,
        choices=(
            (SUPER_ADMIN, '超管'),
            (ADMIN, '管理员'),
            (COMMON, '普通用户'),
        ),
    )
    SALESMAN, BUSINESS, SUPERVISOR, CREATOR = range(4)
    IDENTITY = (
        (SALESMAN, '业务员'),
        (BUSINESS, '商家'),
        (SUPERVISOR, '团队主管'),
        (CREATOR, '视频创作者'),
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
        null=True,
    )
    team = models.ForeignKey(
        # 所属团队
        "users.Team",
        on_delete=models.DO_NOTHING,
        related_name='team_user',
        null=True,
        verbose_name='所属团队'
    )
    has_power = models.BooleanField(
        # 业务员才使用该字段
        _('能否邀请创作者'),
        default=False
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

    is_subscribed = models.BooleanField(
        _("是否已关注公众号"),
        default=False
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
    selling_point = models.TextField(
        verbose_name='商品卖点',
        null=True,
        blank=True
    )

    A, B, C, D, E, F = range(6)
    AGE = (
        (A, '6岁以下'),
        (B, '7-17岁'),
        (C, '18-30岁'),
        (D, '31-45岁'),
        (E, '45-60岁'),
        (F, '60岁以上'),
    )
    group_age = models.PositiveSmallIntegerField(
        _('面向消费群体年龄段'),
        choices=AGE,
        default=A
    )
    group_desc = models.TextField(
        _('面向消费群体自定义说明'),
        null=True,
        blank=True
    )

    MALE, FEMALE, ALL = range(3)
    GENDER = (
        (MALE, '男'),
        (FEMALE, '女'),
        (ALL, '不限'),
    )
    group_gender = models.PositiveSmallIntegerField(
        _('面向消费群体性别'),
        choices=GENDER,
        default=MALE
    )

    point_gender = models.PositiveSmallIntegerField(
        _('拍摄达人侧重点性别'),
        choices=GENDER,
        default=MALE
    )
    style = models.ManyToManyField(
        'CelebrityStyle',
        related_name='bus_style',
        verbose_name='拍摄达人侧重点达人风格'

    )
    script_type = models.ManyToManyField(
        'ScriptType',
        related_name='bus_script',
        verbose_name='拍摄达人侧重点脚本类别'
    )
    style_desc = models.TextField(
        _('达人拍摄重点其他说明'),
        null=True,
        blank=True
    )
    remain_video_num = models.PositiveIntegerField(
        _('剩余视频数'),
        default=0
    )

    class Meta:
        verbose_name = '商家信息'
        verbose_name_plural = verbose_name
        db_table = 'UserBusiness'


class UserCreator(BaseModel):
    """
    创作者信息
    """
    uid = models.OneToOneField(
        "Users",
        to_field='uid',
        on_delete=models.DO_NOTHING,
        related_name='user_creator',
    )
    NOT_CERTIFIED, PENDING, APPROVED, REJECTED = range(4)
    status = models.PositiveSmallIntegerField(
        default=NOT_CERTIFIED,
        choices=(
            (NOT_CERTIFIED, '未认证'),
            (PENDING, '待审核'),
            (APPROVED, '已认证'),
            (REJECTED, '审核不通过'),
        )
    )
    remark = models.CharField(
        verbose_name='工作人员备注(异常备注)',
        max_length=1024,
        null=True,
        blank=True
    )
    video = models.URLField(
        verbose_name="介绍视频",
        max_length=1000,
        null=True
    )
    team_introduction = models.TextField(
        verbose_name="团队介绍",
        null=True
    )
    capability_introduction = models.TextField(
        verbose_name="能力介绍",
        null=True
    )
    is_signed = models.BooleanField(
        verbose_name="是否签约创作者",
        default=False
    )
    contract_reward = models.IntegerField(
        # 合同上签订的酬劳当默认配置，具体订单酬劳可在申请订单表reward字段修改
        _('合同上签订的每条视频可得酬劳'),
        default=0
    )

    class Meta:
        verbose_name = '创作者信息'
        verbose_name_plural = verbose_name
        db_table = 'UserCreator'


class CelebrityStyle(BaseModel):
    title = models.CharField(
        _('风格标题'),
        max_length=50,
        null=True,
    )

    class Meta:
        verbose_name = '达人风格'
        verbose_name_plural = verbose_name
        db_table = 'CelebrityStyle'


class ScriptType(BaseModel):
    title = models.CharField(
        _('脚本类别标题'),
        max_length=50,
        null=True,
    )

    class Meta:
        verbose_name = '脚本类别'
        verbose_name_plural = verbose_name
        db_table = 'ScriptType'


class Team(BaseModel):
    """
    团队
    """
    leader = models.OneToOneField(
        "Users",
        to_field='uid',
        on_delete=models.DO_NOTHING,
        related_name='user_team',
        null=True,
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

    def __str__(self):
        return self.name

    def edit_audit_button(self):
        # 自定义admin按钮
        btn_str = '<a class="btn btn-xs btn-warning" href="{}">' \
                  '<input name="团队成员"' \
                  'type="button" id="passButton" ' \
                  'title="passButton" value="团队成员" class="el-button el-button--primary">' \
                  '</a >'
        return format_html(btn_str, f'/admin/users/teamusers/?team__name={self.name}')

    edit_audit_button.short_description = "操作"


class Address(BaseModel):
    uid = models.ForeignKey(
        "Users",
        to_field='uid',
        on_delete=models.DO_NOTHING,
        related_name='address',
    )
    name = models.CharField(
        _('收货人姓名'),
        max_length=64
    )
    phone = models.CharField(
        _('收货人电话'),
        max_length=11
    )
    province = models.CharField(
        _('所在地省'),
        max_length=128,
        null=True
    )
    city = models.CharField(
        _('所在地市'),
        max_length=128,
        null=True
    )
    district = models.CharField(
        _('所在地地区'),
        max_length=128,
        null=True
    )
    location = models.CharField(
        _('具体地址'),
        max_length=128,
    )
    is_default = models.BooleanField(
        _('是否默认'),
        default=False
    )

    class Meta:
        verbose_name = '地址'
        verbose_name_plural = verbose_name
        ordering = ['-date_created']
