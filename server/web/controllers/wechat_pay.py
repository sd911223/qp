# coding:utf-8

import random
import time
from datetime import datetime

from wechatpy import WeChatPay
from wechatpy.pay.api import WeChatOrder
from wechatpy.utils import timezone

from configs import error
from models import pay_model
from utils import utils
from .base_handler import BaseHandler

APP_ID = 'wx8261604d5039e90b'
PAY_SECRET = '0c59a71bcdb3b3b02fb56e6a20a9f172'
MCH_ID = '1505015271'
NOTIFY_URL = "http://weixinpay.jingangdp.com/Home/WechatAPPTravelactivitieNotify"


class WechatPayHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        params = utils.json_decode(self.get_string('params'))

        pay_type = int(params["paytype"])
        product_id = int(params['productid'])

        if pay_type == 4:
            item = {'Prices': product_id, 'Gifts': 0, 'Numbers': int(product_id) * 10}
        elif pay_type != 3:
            item = pay_model.get_item_by_id(self.share_db(), product_id)
            if not item:
                return self.write_json(error.DATA_BROKEN)
        else:
            item = {'Prices': product_id, 'Gifts': 0, 'Numbers': int(product_id)}
        money = int(item['Prices'] * 100)
        trade_id = '{0}{1}'.format(
            datetime.fromtimestamp(time.time(), tz=timezone('Asia/Shanghai')).strftime('%Y%m%d%H%M%S'),
            random.randint(1000, 10000)
        )

        order_type = pay_type
        if order_type == 2:
            order_type = 1
        elif order_type == 1:
            order_type = 2

        client = WeChatPay(APP_ID, PAY_SECRET, MCH_ID)

        order = WeChatOrder(client)
        i = order.create(trade_type="APP", body="充值", total_fee=str(money), notify_url=NOTIFY_URL,
                         out_trade_no=trade_id)

        # 插入订单
        pay_model.insert_order(self.share_db(), self.uid, trade_id, item['Prices'], order_type, item['Gifts'],
                               product_id, item['Numbers'])

        data = {
            "appid": APP_ID,
            "partnerid": MCH_ID,
            "prepayid": i['prepay_id'],
            "package": "Sign=WXPay",
            "noncestr": i['nonce_str'],
            "timestamp": str(int(time.time()))
        }

        data['sign'] = make_pay_sign(data, PAY_SECRET)
        return self.write_json(error.OK, data)


def make_pay_sign(params, token):
    keys = list(params.keys())
    keys.sort()
    values = []
    for k in keys:
        tmp_str = params[k]
        values.append(k + '=' + tmp_str)
    values.append("key={0}".format(token))
    sign_data = "&".join(values)
    return utils.md5(sign_data).upper()
