import re

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.http import QueryDict, HttpResponseRedirect
from django.utils.html import format_html

from relations.models import InviteRelationManager
from transaction.models import UserPackageRelation
from users.models import Users, UserBase, UserBusiness, Team, UserExtra, CelebrityStyle, ScriptType
from users.services import InviteCls


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    """用户管理"""
    # 定义admin总览里每行的显示信息
    list_display = (
        'username', 'nickname', 'avatars', 'status', 'salesman_username', 'salesman_name',
        'identity', 'package', 'expiration_time', 'date_created', )
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('username', 'salesman_name', 'auth_base__nickname',)
    # 定义过滤器以哪些字段可以搜索
    list_filter = ('status', 'identity', 'date_created')
    # 详情页面展示的字段
    fields = ('username', 'nickname', 'identity', 'salesman_name', 'status', 'reason')
    # 详情页的只读字段
    readonly_fields = ('username', 'nickname', 'identity')
    # 列表页每页展示的条数
    list_per_page = 20

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        queryset = self.model.objects.filter(is_superuser=False)
        return queryset

    def nickname(self, obj):
        return obj.auth_base.nickname

    def avatars(self, obj):
        avatars = obj.auth_base.avatars
        if avatars:
            return format_html(
                '<img src="{}" width="50px"/>',
                avatars,
            )
        return None

    def salesman_username(self, obj):
        # 所属业务员账号
        qs = InviteRelationManager.objects.filter(invitee=obj).first()
        if qs:
            salesman = qs.salesman
            if salesman:
                return qs.salesman.username
            return None
        return None

    def package(self, obj):
        qs = UserPackageRelation.objects.filter(uid=obj).first()
        if qs:
            return qs.package.package_title
        return None

    def expiration_time(self, obj):
        qs = UserPackageRelation.objects.filter(uid=obj).first()
        if qs:
            return qs.expiration_time
        return None

    nickname.short_description = '用户名称'
    avatars.short_description = '头像'
    salesman_username.short_description = '所属业务员账号'
    package.short_description = '购买套餐'
    expiration_time.short_description = '套餐到期时间'


@admin.register(UserBusiness)
class UserBusinessAdmin(admin.ModelAdmin):
    """商家信息"""
    # 定义admin总览里每行的显示信息
    list_display = (
        'username', 'nickname', 'contact', 'bus_name', 'name_abb', 'industry', 'category', 'selling_point', 'date_created', )
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('uid__username', 'uid__auth_base__nickname', 'contact')
    # 定义过滤器以哪些字段可以搜索
    list_filter = ('date_created', )
    # 列表页每页展示的条数
    list_per_page = 20
    # 禁用编辑链接
    list_display_links = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def username(self, obj):
        return obj.uid.username

    def nickname(self, obj):
        return obj.uid.auth_base.nickname

    nickname.short_description = '用户名称'
    username.short_description = '用户账号'


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """团队管理"""
    # 定义admin总览里每行的显示信息
    list_display = (
        'leader_username', 'name', 'number', 'date_created', 'edit_audit_button')
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('leader__username', 'name')
    # 定义过滤器以哪些字段可以搜索
    list_filter = ('date_created', )
    # 列表页每页展示的条数
    list_per_page = 20
    # 详情页的只读字段
    readonly_fields = ('number', 'date_created', )
    # 编辑链接展示字段
    # list_display_links = ('leader_username', 'name', 'number', 'date_created')

    def has_delete_permission(self, request, obj=None):
        return False

    def leader_username(self, obj):
        return obj.leader.username

    def number(self, obj):
        return obj.team_user.count()

    def response_add(self, request, obj, post_url_continue=None):
        response_add = super().response_add(request, obj, post_url_continue=None)
        # 创建团队时把leader加进团队
        leader_uid = request.POST.get('leader')
        leader_obj = Users.objects.get(uid=leader_uid)
        leader_obj.team = obj
        leader_obj.save()
        return response_add

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        # create或update时，外键leader 需要过滤
        context['adminform'].form.fields['leader'].queryset = Users.objects.filter(identity=Users.SUPERVISOR)
        return super(TeamAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    leader_username.short_description = '账号'
    number.short_description = '团队人数'


class TeamUsers(Users):
    class Meta:
        verbose_name = '团队成员'
        verbose_name_plural = verbose_name
        proxy = True


class UsersForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ('username', )

    def clean(self):
        username = self.cleaned_data.get('username')
        phone_re = re.match(r"^1[35678]\d{9}$", username)
        if not phone_re:
            raise forms.ValidationError(u'请输入正确的手机号')
        return self.cleaned_data


@admin.register(TeamUsers)
class TeamUsersAdmin(admin.ModelAdmin):
    """团队成员"""
    # 定义admin总览里每行的显示信息
    list_display = (
        'salesman_username', 'salesman_name', 'team_name', 'leader_username', 'has_power')
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('salesman_username', 'salesman_name')
    # 定义过滤器以哪些字段可以搜索
    list_filter = ('date_created', 'team__name', 'has_power')
    # 列表页每页展示的条数
    list_per_page = 20
    # 详情页的只读字段
    # readonly_fields = ('username', 'password',)
    # 详情页面展示的字段
    fields = ('username', 'password', 'salesman_name', 'team', 'has_power')
    # 禁用编辑链接
    list_display_links = None
    form = UsersForm

    def get_queryset(self, request):
        queryset = self.model.objects.filter(identity=Users.SALESMAN)
        return queryset

    def has_delete_permission(self, request, obj=None):
        return False

    def team_name(self, obj):
        return obj.team.name if obj.team else None

    def leader_username(self, obj):
        return obj.team.leader.username if obj.team else None

    def salesman_username(self, obj):
        return obj.username

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        if not change:
            if form.is_valid():
                user = form.save()
                user.identity = Users.SALESMAN
                user.set_password(form.data.get('password'))
                user.iCode = InviteCls.encode_invite_code(user.id)
                user.save()
                UserExtra.objects.create(uid=user)
                UserBase.objects.create(
                    uid=user,
                    phone=user.username
                )
                leader = Team.objects.get(id=form.data.get('team')).leader
                InviteRelationManager.objects.create(inviter=leader, invitee=user, level=1)
        super().save_model(request, obj, form, change)

    leader_username.short_description = '所属团队账号'
    team_name.short_description = '所属团队名称'
    salesman_username.short_description = '业务员账号'


class TeamLeader(Users):
    class Meta:
        verbose_name = '团队成员'
        verbose_name_plural = verbose_name
        proxy = True


@admin.register(TeamLeader)
class TeamUsersAdmin(admin.ModelAdmin):
    """团队leader"""
    # 定义admin总览里每行的显示信息
    list_display = ('leader_username', 'leader_salesman_name', 'has_power', 'date_created')
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('leader_username', 'leader_salesman_name')
    # 定义过滤器以哪些字段可以搜索
    list_filter = ('has_power', 'date_created',)
    # 列表页每页展示的条数
    list_per_page = 20
    # 详情页面展示的字段
    fields = ('username', 'password', 'salesman_name', 'has_power')
    # 禁用编辑链接
    list_display_links = None
    form = UsersForm

    def get_queryset(self, request):
        queryset = self.model.objects.filter(identity=Users.SUPERVISOR)
        return queryset

    def has_delete_permission(self, request, obj=None):
        return False

    def leader_username(self, obj):
        return obj.username

    def leader_salesman_name(self, obj):
        return obj.salesman_name

    leader_username.short_description = '业务员主管账号'
    leader_salesman_name.short_description = '业务员名称'

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        if not change:
            if form.is_valid():
                user = form.save()
                user.identity = Users.SUPERVISOR
                user.set_password(form.data.get('password'))
                user.iCode = InviteCls.encode_invite_code(user.id)
                user.save()
                UserExtra.objects.create(uid=user)
                UserBase.objects.create(
                    uid=user,
                    phone=user.username
                )
        else:
            super().save_model(request, obj, form, change)


@admin.register(CelebrityStyle)
class CelebrityStyleAdmin(admin.ModelAdmin):
    """商家信息风格标题"""
    # 定义admin总览里每行的显示信息
    list_display = ('id', 'title', 'date_created')
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('title',)
    # 详情页面展示的字段
    fields = ('title', )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ScriptType)
class CelebrityStyleAdmin(admin.ModelAdmin):
    """商家信息脚本类别"""
    # 定义admin总览里每行的显示信息
    list_display = ('id', 'title', 'date_created')
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('title',)
    # 详情页面展示的字段
    fields = ('title',)

    def has_delete_permission(self, request, obj=None):
        return False
