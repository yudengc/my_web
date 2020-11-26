import abc
import json
import logging
import random
import re
import time
from decimal import Decimal
from urllib import parse

import demjson
import requests
from django.conf import settings

from demand.models import VideoNeeded
from libs.decorator import try_decorator
from libs.tbk import GetTBKCouponInfo

oTbPattern = re.compile('^https://(.*)[.|/]taobao.com')
oJdPattern = re.compile('^https://(.*)[.|/]jd.com')
oKaolaPattern = re.compile('^https://(.*)[.|/]kaola.com')
oTmallPattern = re.compile('^https://(.*)[.|/]tmall.com')
oTmallHkPattern = re.compile('^https://(.*)[.|/]tmall.hk')
oXiaoDianPattern = re.compile('^https://(.*)haohuo')
oXiaoDianShortPattern = re.compile('^https://(.*)douyin')
oYouZanPattern = re.compile('^https://(.*)youzan.com')
logger = logging.getLogger()


class BaseService(metaclass=abc.ABCMeta):

    def __init__(self):
        self.m_ApiMap = {
            'tb': [
                'https://acs.m.taobao.com/h5/mtop.taobao.detail.getdetail/6.0/?'
                'data=%7B"itemNumId"%3A"%s"%7D&qq-pf-to=pcqq.group&name="zhgangsan"',
                'https://acs.m.taobao.com/h5/mtop.taobao.detail.getdetail/6.0/?'
                'data=%7B"itemNumId"%3A"%s"%7D&qq-pf-to=pcqq.group&name="lisi"',
                'https://acs.m.taobao.com/h5/mtop.taobao.detail.getdetail/6.0/?'
                'data=%7B"itemNumId"%3A"%s"%7D&qq-pf-to=pcqq.group&name="wangwu"',
            ]
        }
        self.tb_h5_url = 'https://h5api.m.taobao.com/h5/mtop.taobao.detail.getdesc/6.0/'
        self.kl_url = 'https://m-goods.kaola.com/product/getGoodsAttachment.json'
        self.xd_url = 'https://ec.snssdk.com/product/fxgajaxstaticitem'
        self.vip_url = 'https://mapi.vip.com/vips-mobile/rest/shopping/wap/product/detail/v5'
        self.m_Headers = {'content-type': 'application/json'}

    @abc.abstractmethod
    def get_detail_image(self, *args, **kwargs):
        pass


class TBService(BaseService):
    """淘宝"""

    def __init__(self, goods_id):
        super(TBService, self).__init__()
        self.goods_id = goods_id

    @classmethod
    def get_goods_id(cls, url):
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
            "cookie": "t=c1e8231792f007e72593175d60586f3a; cna=HthOFWZZfEoCAZkiYyMw5eUw; hng=CN%7Czh-CN%7CCNY%7C156; thw=cn; tracknick=tb313659628; lgc=tb313659628; tg=0; enc=C%2B2%2F0QsEwiUFmf00owySlc7hJiEsY4t4EIGdIzzH6ih9ajzhcMJCs7wzlX4%2B4gJrv2IlLviuxk0B1VAXlVwD8Q%3D%3D; x=e%3D1%26p%3D*%26s%3D0%26c%3D0%26f%3D0%26g%3D0%26t%3D0%26__ll%3D-1%26_ato%3D0; miid=1314040285196636905; uc3=vt3=F8dBy3vI3wKCeS4bgiY%3D&id2=VyyWskFTTiu0DA%3D%3D&nk2=F5RGNwsJzCC9CC4%3D&lg2=Vq8l%2BKCLz3%2F65A%3D%3D; _cc_=VFC%2FuZ9ajQ%3D%3D; _m_h5_tk=ec90707af142ccf8ce83ead2feda4969_1560657185501; _m_h5_tk_enc=2bc06ae5460366b0574ed70da887384e; mt=ci=-1_0; cookie2=14c413b3748cc81714471780a70976ec; v=0; _tb_token_=e33ef3765ebe5; alitrackid=www.taobao.com; lastalitrackid=www.taobao.com; swfstore=97544; JSESSIONID=80EAAE22FC218875CFF8AC3162273ABF; uc1=cookie14=UoTaGdxLydcugw%3D%3D; l=bBjUTZ8cvDlwwyKtBOCNCuI8Li7OsIRAguPRwC4Xi_5Z86L6Zg7OkX_2fFp6Vj5RsX8B41jxjk99-etki; isg=BP__g37OnjviDJvk_MB_0lRbjtNJTFLqmxNfMJHMlK71oB8imbTI1uey5jD7-Cv-"
        }
        if url.find('&id=') == -1 and url.find('?id=') == -1:
            url = requests.get(url, headers=headers, verify=False).url
        query = parse.parse_qs(parse.urlparse(url).query)
        if 'id' in query.keys():
            return query['id'][0], url
        return '', url

    def get_requests_data(self):
        m_api_url = random.choice(self.m_ApiMap['tb']).replace("%s", str(self.goods_id))
        res = requests.get(m_api_url, self.m_Headers, verify=False)
        data = res.json().get('data')
        return data

    @try_decorator
    def get_detail_image(self):
        """详情图"""
        data = self.get_requests_data()
        if 'item' in data.keys():
            image_url = data['item'].get('tmallDescUrl', data.get('taobaoDescUrl'))
            if not image_url.startswith('http'):
                image_url = 'https:' + image_url
            return self.get_img_list(image_url)
        return []

    # @try_decorator
    # def tb_shop_info(self):
    #     data = self.get_requests_data()['seller']
    #     shop_name = data.get('shopName')
    #     shop_id = data.get('shopId')
    #     # 卖家服务
    #     sell_score = 4.0
    #     # 宝贝描述
    #     desc_score = 4.0
    #     # 物流服务
    #     send_score = 4.0
    #     if data.get('shopIcon'):
    #         shop_logo = 'http:' + data.get('shopIcon') if not data.get('shopIcon').startswith('http') else data.get(
    #             'shopIcon')
    #     else:
    #         shop_logo = ''
    #     evaluates = data.get("evaluates")
    #     for dDetail in evaluates:
    #         if dDetail['title'] == u'宝贝描述':
    #             desc_score = dDetail['score']
    #         elif dDetail['title'] == u'卖家服务':
    #             sell_score = dDetail['score']
    #         elif dDetail['title'] == u'物流服务' or dDetail['title'] == u'跨境物流':
    #             send_score = dDetail['score']
    #     return self.verify_shop(shop_id, shop_name, shop_logo, sell_score, send_score, desc_score)

    def get_img_list(self, item_image_url):
        req = requests.get(item_image_url)
        desc_json = demjson.decode(re.search(r'Desc.init\(([\D\d]*?)\);', req.text).group(1))['TDetail']
        res_list = []
        try:
            for data in desc_json['api']['newWapDescJson']:
                if 'data' in data.keys():
                    img_list = data['data']
                    for i in img_list:
                        img = i['img']
                        img_url = 'https:' + img if not img.startswith('http') else img
                        res_list.append(img_url)
        except KeyError:
            url = self.tb_h5_url
            params = {
                'appKey': 12574478,
                't': str(int(time.time())),
                'api': 'mtop.taobao.detail.getdesc',
                'data': json.dumps({"id": self.goods_id, "type": "1"})
            }
            res = requests.get(url, params=params).json()
            html = res["data"]["pcDescContent"]
            url_list = re.findall(r'//[^\"]+[0-9].jpg', html)
            res_list = ["https:" + url if not url.startswith('http') else url for url in url_list]
        return res_list

    @try_decorator
    def get_master_images(self):
        """主图"""
        # Todo 商品已下架的情况未考虑，现在无时间，以后在加上
        data = self.get_requests_data()
        images = data['item']['images']
        image_list = ['https:' + image if not image.startswith('http') else image for image in images]
        return image_list

    @try_decorator
    def get_title_price(self):
        good_amount_info = GetTBKCouponInfo().my_custom_api(num_iids=self.goods_id, method='taobao.tbk.item.info.get')
        if good_amount_info.get('error_response', False):
            price = 0
            title = ''
        else:
            goods_info = good_amount_info['tbk_item_info_get_response']['results']['n_tbk_item'][0]
            price = goods_info['zk_final_price']
            title = goods_info['title']
        return title, price

    # def verify_shop(self, shop_id, shop_name, shop_logo, sell_score, send_score=4.0, desc_score=4.0):
    #     t, _ = Shops.objects.update_or_create(
    #         shop_id=shop_id,
    #         defaults={
    #             'name': shop_name,
    #             'icon': shop_logo,
    #             'sell_service_score': sell_score,
    #             'send_service_score': send_score,
    #             'desc_score': desc_score
    #         }
    #     )
    #     return t.id

    def get_goods_detail(self, text=False):
        """好单库超级搜索api获取tb商品详情"""
        encode_goods_id = parse.quote(self.goods_id)
        url = f'http://v2.api.haodanku.com/supersearch/apikey/{settings.HDK_API_KEY}/keyword/{encode_goods_id}/back/10/' \
              f'min_id/1/tb_p/1/sort/0/is_tmall/0/is_coupon/0/limitrate/0'
        if text:
            return requests.get(url).text
        return requests.get(url).json()


class XDSpiderService:
    """抖音小店（用的是爬虫接口）"""

    def __init__(self, goods_link):
        self.goods_link = goods_link
        self.headers = {"Content-Type": "application/json;charset=UTF-8"}

    def get_goods_detail(self):
        try:
            res = requests.post(url=settings.DY_CHECK_GOODS_URL,
                                json={'link': self.goods_link},
                                headers=self.headers,
                                timeout=3.5)
        except Exception as e:
            logger.info('抖音小店接口第一次请求报错了')
            logger.info(e)
            try:
                res = requests.post(url=settings.DY_CHECK_GOODS_URL,
                                    json={'link': self.goods_link},
                                    headers=self.headers,
                                    timeout=6)
            except Exception as e:
                logger.info('抖音小店接口第二次请求报错了')
                logger.info(e)
                return '请求报错'
        return res.json()

    def get_shop_detail(self):
        #  抖音店铺信息和商品详情图
        try:
            res = requests.post(url=settings.DY_CHECK_SHOP_URL,
                                json={'link': self.goods_link},
                                headers=self.headers,
                                timeout=20)
        except Exception as e:
            logger.info('抖音店铺信息接口第一次请求报错了')
            logger.info(e)
            try:
                res = requests.post(url=settings.DY_CHECK_SHOP_URL,
                                    json={'link': self.goods_link},
                                    headers=self.headers,
                                    timeout=20)
            except Exception as e:
                logger.info('抖音店铺信息接口第二次请求报错了')
                logger.info(e)
                return '请求报错'
        return res.json()


class CheckLinkError(Exception):
    """
    链接错误
    """

    def __init__(self, err):
        super(CheckLinkError, self).__init__(err)


class CheckLinkRequestError(Exception):
    """
    请求错误
    """

    def __init__(self, err):
        super(CheckLinkRequestError, self).__init__(err)


def check_link_and_get_data(goods_link):
    if oTbPattern.search(goods_link) or oTmallPattern.search(goods_link) or oTmallHkPattern.search(
            goods_link):
        goods_id, url = TBService.get_goods_id(goods_link)
        try:
            _goods_data = None
            _goods_data = TBService(goods_id).get_goods_detail(text=True)
            goods_data = json.loads(_goods_data)
            if goods_data.get('code') != 1:
                return 444
        except Exception as e:
            logger.info('获取商品详情接口返回数据(text):')
            logger.info(_goods_data)
            logger.info('goods_id')
            logger.info(goods_id)
            logger.info(e)
            raise CheckLinkRequestError('调用获取商品detail报错, 请联系技术人员处理!')
        data = goods_data.get('data')[0]
        data['channel'] = VideoNeeded.TB  # 淘宝
        return data
    elif oXiaoDianPattern.search(goods_link) or oXiaoDianShortPattern.search(goods_link):
        data = XDSpiderService(goods_link).get_goods_detail()
        if data == '请求报错':
            raise CheckLinkError('获取商品信息失败，请重试')
        if data.get('status_code') == 200:
            if data.get('detail_product_res') == 'success':
                goods_data = data.get('goods_dict')
                if goods_data:
                    dic = dict(tkrates=goods_data.get('cos_radio'), itemid=goods_data.get('goods_id'),
                               itemtitle=goods_data.get('title'),
                               itempic=goods_data.get('cover_url'), itemsale=goods_data.get('sales'),
                               channel=VideoNeeded.DY,
                               itemprice=Decimal(str(goods_data.get('price'))) * Decimal(str(0.01)), )
                    return dic
                else:
                    raise CheckLinkError('获取商品信息失败了')
            elif re.compile(r'您还未绑定淘宝客PID').search(data.get('detail_product_res')):
                raise CheckLinkError('抱歉，您的商品链接有误，请确定是淘宝或者抖音商品链接')
            elif re.compile(r'未识别该商品').search(data.get('detail_product_res')):
                raise CheckLinkError('抱歉，该商品不能在抖音上架')
            elif re.compile(r'没有搜索到您想要的精选联盟商品').search(data.get('detail_product_res')):
                raise CheckLinkError('没有搜索到您想要的精选联盟商品哦，请检查链接或者更换一个商品吧')
            else:
                raise CheckLinkError('获取商品信息失败')
        else:
            raise CheckLinkRequestError('获取商品信息失败，请重试')
    else:
        raise CheckLinkError('抱歉，非淘宝或抖音小店的商品暂时不能上架')
