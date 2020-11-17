from django.contrib import admin
from django.http import QueryDict
from django.utils.html import format_html

from relations.models import InviteRelationManager
from transaction.models import UserPackageRelation
from users.models import Users, UserBase, UserBusiness


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    """用户管理"""
    # 定义admin总览里每行的显示信息
    list_display = (
        'username', 'nickname', 'avatars', 'status', 'salesman_username', 'salesman_name',
        'identity', 'package', 'expiration_time', 'date_created', )
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('username', 'salesman_name', 'auth_base__nickname', 'user_salesman__username')
    # 定义过滤器以哪些字段可以搜索
    list_filter = ('status', 'identity', 'date_created')
    # 详情页面展示的字段
    fields = ('username', 'nickname', 'identity', 'salesman_name', 'status', 'reason')
    # 详情页的只读字段
    readonly_fields = ('username', 'nickname')
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
        return format_html(
            '<img src="{}" width="50px"/>',
            obj.auth_base.avatars,
        )

    def salesman_username(self, obj):
        # 所属业务员账号
        qs = InviteRelationManager.objects.filter(invitee=obj).first()
        if qs:
            return qs.salesman.username
        return None

    def package(self, obj):
        qs = UserPackageRelation.objects.filter(uid=obj).first()
        if qs:
            return qs.package.package_title
        return None

    def expiration_time(self, obj):
        qs = UserPackageRelation.objects.filter(uid=obj).first()
        if qs:
            return qs.package.expiration_time
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
        'username', 'nickname', 'contact', 'bus_name', 'name_abb', 'industry', 'category', 'desc', 'date_created', )
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

    def get_actions(self, request):
        # 在actions中去掉‘删除'操作
        actions = super(UserBusinessAdmin, self).get_actions(request)
        # if request.user.username[0].upper() != 'J':
        #     if 'delete_selected' in actions:
        #         del actions['delete_selected']
        print(actions)
        return actions

    def username(self, obj):
        return obj.uid.username

    def nickname(self, obj):
        return obj.uid.auth_base.nickname

    nickname.short_description = '用户名称'
    username.short_description = '用户账号'
