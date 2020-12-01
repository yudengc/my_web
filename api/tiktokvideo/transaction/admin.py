from django.contrib import admin

from relations.models import InviteRelationManager
from transaction.models import Package, UserPackageRelation


@admin.register(Package)
class UsersAdmin(admin.ModelAdmin):
    """商家套餐管理"""
    # 定义admin总览里每行的显示信息
    list_display = (
        'package_title', 'package_amount', 'expiration', 'status', 'package_content', 'date_created', )
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('package_title',)
    # 定义过滤器以哪些字段可以搜索
    list_filter = ('status', 'date_created')
    # 详情页面展示的字段
    fields = ('package_title', 'package_amount', 'status', 'package_content', 'expiration')
    # 列表页每页展示的条数
    list_per_page = 20

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserPackageRelation)
class UserPackageRelationAdmin(admin.ModelAdmin):
    """套餐购买记录"""
    # 定义admin总览里每行的显示信息
    list_display = (
        'username', 'nickname', 'salesman_username', 'salesman_name', 'package_title', 'package_amount', 'status',
        'date_created',)
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('uid__username', 'uid__auth_base__nickname')
    # 定义过滤器以哪些字段可以搜索
    list_filter = ('status', 'date_created')
    # 详情页面展示的字段
    fields = ('username', 'nickname', 'salesman_username', 'status')
    # 详情页的只读字段
    readonly_fields = ('username', 'nickname', 'salesman_username')
    # 列表页每页展示的条数
    list_per_page = 20

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def username(self, obj):
        return obj.uid.username

    def nickname(self, obj):
        return obj.uid.auth_base.nickname

    def salesman_username(self, obj):
        r_obj = InviteRelationManager.objects.filter(invitee=obj.uid).first()
        if r_obj:
            salesman = r_obj.salesman
            if salesman:
                return salesman.username
            return None
        else:
            return None

    def salesman_name(self, obj):
        r_obj = InviteRelationManager.objects.filter(invitee=obj.uid).first()
        if r_obj:
            salesman = r_obj.salesman
            if salesman:
                return salesman.salesman_name
            return None
        else:
            return None

    def package_title(self, obj):
        return obj.package.package_title

    def package_amount(self, obj):
        return obj.package.package_amount

    username.short_description = '用户账号'
    nickname.short_description = '用户名称'
    salesman_username.short_description = '所属业务员账号'
    salesman_name.short_description = '业务员名称'
    package_title.short_description = '套餐名称'
    package_amount.short_description = '套餐金额'
