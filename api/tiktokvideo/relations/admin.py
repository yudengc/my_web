from django.contrib import admin

from relations.models import InviteRelationManager


@admin.register(InviteRelationManager)
class RelationAdmin(admin.ModelAdmin):
    """邀请关系"""
    # 定义admin总览里每行的显示信息
    list_display = ('invitee_username', 'invitee_nickname', 'invitee_role', 'inviter_username', 'inviter_nickname',
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

    def invitee_role(self, obj):
        identity = obj.invitee.identity
        if identity == 0:
            data = '业务员'
        elif identity == 1:
            data = '商家'
        elif identity == 2:
            data = '主管'
        else:
            return None
        return data

    def inviter_username(self, obj):
        return obj.inviter.username

    def inviter_nickname(self, obj):
        return obj.inviter.auth_base.nickname

    def salesman_username(self, obj):
        salesman = obj.salesman
        if salesman:
            return salesman.username
        return None

    def salesman_nickname(self, obj):
        salesman = obj.salesman
        if salesman:
            return obj.salesman.auth_base.nickname
        return None

    def time(self, obj):
        return obj.date_created

    invitee_username.short_description = '被邀请人账号'
    invitee_nickname.short_description = '被邀请人名称'
    inviter_username.short_description = '邀请人账号'
    inviter_nickname.short_description = '邀请人名称'
    salesman_username.short_description = '所属业务员账号'
    salesman_nickname.short_description = '所属业务员名称'
    time.short_description = '邀请时间'
    invitee_role.short_description = '被邀请人角色'
