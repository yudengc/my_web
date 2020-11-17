from django.contrib import admin
from django.utils.html import format_html

from config.models import CustomerService


@admin.register(CustomerService)
class UsersAdmin(admin.ModelAdmin):
    """用户管理"""
    # 定义admin总览里每行的显示信息
    list_display = ('name', 'weChat_num', 'qr', 'date_created')
    # 列表页每页展示的条数
    list_per_page = 10

    def has_delete_permission(self, request, obj=None):
        return False

    def qr(self, obj):
        return format_html(
            '<img src="{}" width="120px"/>',
            obj.qr_code,
        )

    qr.short_description = '微信二维码'
