from django.contrib import admin

# Register your models here.
from permissions.models import PermissionsBase


@admin.register(PermissionsBase)
class PermissionsBaseAdmin(admin.ModelAdmin):
    """
    权限配置
    """
    # 定义admin总览里每行的显示信息
    list_display = (
        'id', 'name', 'path', 'category', 'pid', 'order_num', 'is_active',)
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('name',)
    # 定义过滤器以哪些字段可以搜索
    list_filter = ('is_active', 'category',)
    # 列表可以编辑的字段
    # list_editable = ('status',)
    # 是否开启显示选中数量
    actions_selection_counter = True
    # 根据时间段, 去过滤数据
    # date_hierarchy = 'date_created'
    # 每页显示个数
    list_per_page = 20

    # fields = ('uid', 'nickname', 'gender', 'fans_count', 'sys_remark', 'date_created',)
    def has_delete_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return True

    fieldsets = (
        ['权限详情', {
            'fields': (
                'name', 'path', 'category', 'pid', 'order_num', 'is_active',
            ),
        }],
    )
