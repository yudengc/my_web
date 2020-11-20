from django.contrib import admin

from relations.models import InviteRelationManager


@admin.register(InviteRelationManager)
class RelationAdmin(admin.ModelAdmin):
    """用户管理"""
    # 定义admin总览里每行的显示信息
    list_display = ('invitee_username', 'invitee_nickname', 'inviter_username', 'inviter_nickname',
                    'salesman_username', 'salesman_nickname', 'time')
    # 定义搜索框以哪些字段可以搜索
    search_fields = ('inviter__username', 'inviter__auth_base__nickname', 'invitee__username', 'invitee__auth_base__nickname')
    # 定义过滤器以哪些字段可以搜索
    # list_filter = ()
    # 列表页每页展示的条数
    list_per_page = 20
    # 禁用详情页
    list_display_links = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def invitee_username(self, obj):
        return obj.invitee.username

    def invitee_nickname(self, obj):
        return obj.invitee.auth_base.nickname

    def inviter_username(self, obj):
        return obj.inviter.username

    def inviter_nickname(self, obj):
        return obj.inviter.auth_base.nickname

    def salesman_username(self, obj):
        return obj.salesman.username

    def salesman_nickname(self, obj):
        return obj.salesman.auth_base.nickname

    def time(self, obj):
        return obj.date_created

    invitee_username.short_description = '用户账号'
    invitee_nickname.short_description = '用户名称'
    inviter_username.short_description = '邀请人账号'
    inviter_nickname.short_description = '邀请人名称'
    salesman_username.short_description = '所属业务员账号'
    salesman_nickname.short_description = '所属业务员名称'
    time.short_description = '邀请时间'
