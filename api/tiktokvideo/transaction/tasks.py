import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.db.transaction import atomic

from transaction.models import OrderInfo, UserPackageRelation, Package
from users.models import Users, UserBusiness

logger = logging.getLogger()


# @shared_task
def update_order_status(out_trade_no, gmt_payment, attach):
    order = OrderInfo.objects.filter(out_trade_no=out_trade_no)
    # print("======= Pay Success And Update Order Status =======")
    logger.info("======= Pay Success And Update Order Status =======")
    if order.exists():
        with atomic():
            order_info = OrderInfo.objects.filter(out_trade_no=out_trade_no, status=OrderInfo.WAIT).update(
                status=OrderInfo.SUCCESS,
                date_payed=gmt_payment
            )
            if order_info == 0:
                logger.info('更新订单状态失败')
            else:
                this_man = order.first.uid
                parm_lis = attach.split('_')
                logger.info(parm_lis)
                p_obj = Package.objects.get(id=parm_lis[1])
                expiration = p_obj.expiration  # 套餐有效天数
                try:
                    r_obj = UserPackageRelation.objects.get(uid=this_man, package=p_obj)
                    if r_obj.expiration_time > datetime.now():  # 未过期
                        r_obj.expiration_time += timedelta(days=expiration)
                    else:  # 已过期
                        r_obj.expiration_time = datetime.now() + timedelta(days=expiration)
                    r_obj.save()
                except UserPackageRelation.DoesNotExist:
                    UserPackageRelation.objects.create(uid=this_man,
                                                       package=p_obj,
                                                       expiration_time=datetime.now() + timedelta(days=expiration))
                # 商家购买套餐赠与视频数
                business_qs = UserBusiness.objects.filter(uid=this_man)
                if not business_qs.exists():
                    UserBusiness.objects.create(uid=this_man)
                this_man.user_business.remain_video_num += p_obj.video_num
                this_man.user_business.save()

        logger.info("======= Pay Success And Update Order Status!!!!!! =======")
    else:
        logger.info('找不到订单，订单号：%s' % out_trade_no)
