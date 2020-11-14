from celery import shared_task
from django.db.transaction import atomic

from transaction.models import OrderInfo, UserPackageRelation


@shared_task
def update_order_status(out_trade_no, gmt_payment, attach):
    order = OrderInfo.objects.filter(out_trade_no=out_trade_no)
    print("======= Pay Success And Update Order Status =======")
    if order.exists():
        with atomic():
            order_info = OrderInfo.objects.filter(out_trade_no=out_trade_no, status=OrderInfo.WAIT).update(
                status=OrderInfo.SUCCESS,
                pay_time=gmt_payment
            )
            if order_info == 0:
                print('更新订单状态失败')
            else:
                parm_lis = attach.split('_')
                UserPackageRelation.objects.create(order_number=out_trade_no, uid=parm_lis[0], package=parm_lis[1])
    else:
        print('找不到订单，订单号：%s' % out_trade_no)
