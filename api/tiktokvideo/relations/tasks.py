import logging

from celery import shared_task

from relations.models import InviteRelationManager
from users.models import Users


logger = logging.getLogger()


# @shared_task
def save_invite_relation(code, phone):
    """
    存储邀请关系
    :param code: 邀请者code
    :param phone: 被邀请者账号
    :return:
    """
    # print("======= Start Save Invite Relation =======")
    logger.info("======= Start Save Invite Relation =======")
    inviter_user = Users.objects.filter(iCode=code).first()   # 邀请者
    inviter_identity = inviter_user.identity  # 邀请者的角色，0：业务员，1：商家
    invitee_user = Users.objects.filter(username=phone).first()   # 被邀请者
    if not inviter_user:
        # print('iCode错误')
        logger.info('iCode错误')
        return
    if InviteRelationManager.objects.filter(invitee=invitee_user).exists():
        # 已被邀请过无需再保存
        return

    # 查询邀请者是否拥有上级
    inviter_queryset = InviteRelationManager.objects.filter(invitee=inviter_user)
    try:
        if inviter_queryset.exists():
            # 存在上级，如果上级也是业务员（即邀请者是老大A，被邀请者是下属B,下属账号是在后台创建的），则无需记录salesman字段
            for instance in inviter_queryset:
                invitee = invitee_user
                salesman = instance.salesman   # 业务员
                level = instance.level + 1
                superior = f'{instance.superior}|{inviter_user.id}'
                if inviter_identity == Users.SALESMAN:   # 邀请者为业务员（即上级是老大A,邀请者自己是下属B），则salesman字段记录邀请者
                    InviteRelationManager(
                        inviter=inviter_user,
                        invitee=invitee,
                        level=level,
                        salesman=inviter_user,
                        superior=superior
                    ).save()
                elif inviter_identity == Users.BUSINESS:  # 邀请者为商家，则salesman字段与上一级的salesman保持一致
                    InviteRelationManager(
                        inviter=inviter_user,
                        invitee=invitee,
                        level=level,
                        salesman=salesman,
                        superior=superior
                    ).save()
        else:  # 不存在上级（团队老大）, 业务员即邀请者
            InviteRelationManager(
                inviter=inviter_user,
                invitee=invitee_user,
                level=1,
                salesman=inviter_user,
                superior=inviter_user.id
            ).save()
            # print("======= END =======")
            logger.info("======= END =======")
    except Exception as e:
        # print("Error: ", e)
        logger.info("Error: ", e)
