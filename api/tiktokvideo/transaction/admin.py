from django.contrib import admin

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
        'package_title', 'package_amount', 'expiration', 'status', 'package_content', 'date_created',)
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

    def has_add_permission(self, request):
        return False

    def username(self, obj):
        return obj.uid.username

    def nickname(self, obj):
        return obj.uid.auth_base.nickname

    def salesmales_username(self, obj):
        return
