import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.db.transaction import atomic

from transaction.models import OrderInfo, UserPackageRelation, Package, UserPackageRecord
from users.models import Users, UserBusiness

logger = logging.getLogger()


@shared_task
def update_order_status(out_trade_no, gmt_payment, attach):
    order = OrderInfo.objects.filter(out_trade_no=out_trade_no)
    print("======= Pay Success And Update Order Status =======")
    # logger.info("======= Pay Success And Update Order Status =======")
    if order.exists():
        with atomic():
            order_info = OrderInfo.objects.filter(out_trade_no=out_trade_no, status=OrderInfo.WAIT).update(
                status=OrderInfo.SUCCESS,
                date_payed=gmt_payment
            )
            if order_info == 0:
                # logger.info('更新订单状态失败')
                print('更新订单状态失败')
            else:
                this_man = order.first().uid
                parm_lis = attach.split('_')
                logger.info(parm_lis)
                p_obj = Package.objects.get(id=parm_lis[1])
                expiration = p_obj.expiration  # 套餐有效天数

                r_obj = UserPackageRelation.objects.filter(uid=this_man, package=p_obj).first()
                if r_obj:
                    if r_obj.expiration_time > datetime.now():  # 未过期
                        r_obj.expiration_time += timedelta(days=expiration)
                    else:  # 已过期
                        r_obj.expiration_time = datetime.now() + timedelta(days=expiration)
                    r_obj.save()
                else:
                    UserPackageRelation.objects.create(uid=this_man,
                                                       package=p_obj,
                                                       expiration_time=datetime.now() + timedelta(days=expiration))
                # 商家购买套餐赠与视频数
                business_qs = UserBusiness.objects.filter(uid=this_man)
                if not business_qs.exists():
                    UserBusiness.objects.create(uid=this_man)
                this_man.user_business.remain_video_num += p_obj.video_num + p_obj.buy_video_num
                this_man.user_business.save()
                UserPackageRecord.objects.create(uid=this_man,
                                                 package_id=p_obj.id,
                                                 package_title=p_obj.package_title,
                                                 package_amount=p_obj.package_amount,
                                                 package_content=p_obj.package_content,
                                                 expiration=p_obj.expiration,
                                                 buy_video_num=p_obj.buy_video_num,
                                                 video_num=p_obj.video_num)

        # logger.info("======= Pay Success And Update Order Status!!!!!! =======")
        print("======= Pay Success And Update Order Status!!!!!! =======")
    else:
        # logger.info('找不到订单，订单号：%s' % out_trade_no)
        print('找不到订单，订单号：%s' % out_trade_no)
