# coding:utf-8

import tornado
import base64
from .base_handler import BaseHandler
from utils import utils
from configs import error, config, const
from models import iap_model, player_model


class IAPHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        self.finish('empty method')

    @tornado.web.asynchronous
    def post(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('ticket'):
            return self.write_json(error.DATA_BROKEN)

        if not self.share_db() or not self.share_db_logs():
            return self.write_json(error.SYSTEM_ERR)

        ticket = params.get('ticket')
        receipt = ticket.get('receipt')
        order_id = str(receipt.get('transactionIdentifier'))

        if not ticket or not receipt or not self.uid or not order_id:
            return self.write_json(error.DATA_BROKEN)

        order = iap_model.get_by_oid(self.share_db(), order_id)
        if not order:
            # 创建订单
            is_sandbox = int(self.get_string('params').find('Sandbox') != -1)
            iap_model.create_order(self.share_db(), self.uid, order_id, self.get_string('params'),
                                   str(receipt['productIdentifier']), 1, is_sandbox, 0)

        elif order.status > 0:
            return self.write_json(error.SYSTEM_ERR)

        def on_success(verify_data):
            ret_data = utils.json_decode(verify_data)
            if not ret_data or ret_data['status'] != 0:
                return self.write_json(error.SYSTEM_ERR)

            # 将返回数据 写入 IAP 表
            receipt_json = ret_data['receipt']
            iap_model.modify_data_and_status_by_oid(self.share_db(), verify_data, 1,
                                                    receipt_json['transaction_id'])

            # 从配置文件中获取相应增加的钻石
            diamond = config.get_iap_by_item(receipt_json['product_id'])
            if not diamond:
                diamond = 2

            # 用户添加对应钻石
            left_diamonds = player_model.get_by_uid(self.share_db(), self.uid).get('diamond', 0)
            total_diamonds = left_diamonds + diamond
            player_model.add_diamonds_with_log(self.share_db(), self.share_db_logs(), self.uid, diamond,
                                               0, "", const.REASON_IAP, total_diamonds)

            return self.write_json(error.OK, {"diamond": total_diamonds})

        def on_fail():
            self.write_json(error.SYSTEM_ERR)

        url_production = "https://buy.itunes.apple.com/verifyReceipt"
        url_sandbox = "https://sandbox.itunes.apple.com/verifyReceipt"
        url = url_production if self.get_string('params').find('Sandbox') == -1 else url_sandbox
        base_data = base64.b64encode(str(receipt.get('receipt')).encode('ascii'))
        data = '{"receipt-data" : "%s"}' % base_data.decode('ascii')
        utils.http_post(url, {}, on_success, on_fail, body=data)
