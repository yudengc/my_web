from django.db import models
from django.utils.translation import ugettext_lazy as _
from users.models import BaseModel


class InviteRelationManager(BaseModel):
    inviter = models.ForeignKey(
        # 邀请者
        'users.Users',
        related_name="user_inviter",
        on_delete=models.DO_NOTHING,
    )
    invitee = models.ForeignKey(
        # 被邀请者
        'users.Users',
        related_name="user_invitee",
        on_delete=models.DO_NOTHING,
    )
    salesman = models.ForeignKey(
        # 所属业务员
        'users.Users',
        related_name="user_salesman",
        on_delete=models.DO_NOTHING,
        null=True,
    )
    level = models.PositiveIntegerField(
        _('等级关系'),
        default=0
    )
    superior = models.CharField(
        null=True,
        blank=True,
        default=''
    )
    UNTREATED, PROCESSED = range(2)
    STATUS = (
        (UNTREATED, '待跟进'),
        (PROCESSED, '已跟进'),
    )
    status = models.PositiveSmallIntegerField(
        _('状态'),
        choices=STATUS,
        default=UNTREATED
    )

    class Meta:
        verbose_name = '邀请关系'
        verbose_name_plural = verbose_name
        db_table = 'InviteRelation'
        unique_together = (
            ('inviter', 'invitee')
        )
