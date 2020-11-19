# coding:utf-8

import random
import time
from datetime import datetime

from wechatpy.utils import timezone

from configs import error, const
from models import player_model, money_model, database
from utils import utils
from .base_handler import BaseHandler


class GetAddressHandler(BaseHandler):
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
        data = player_model.get_address(self.share_db(), self.uid)
        return self.write_json(error.OK, data)


class ChangeYuanBaoToDiamond(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def __calc_change_count(self, count):
        extra_count = 0
        yuan_bao = count
        return extra_count, yuan_bao

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('count'):
            return self.write_json(error.DATA_BROKEN)

        count = int(params['count'])
        if count <= 0:
            return self.write_json(error.DATA_BROKEN)
        status = player_model.change_yuan_bao_to_diamond(self.share_db(), self.uid, count)
        if status == 0:
            return self.write_json(error.DIAMONDS_NOT_ENOUGH)

        extra_count, yuan_bao = self.__calc_change_count(count)
        player_model.write_change_yuan_bao_to_diamond_logs(self.share_db_logs(), self.uid, count, extra_count, yuan_bao)
        return self.write_json(error.OK, {"diamond": count, "extraDiamond": extra_count, "yuanBao": yuan_bao})


class ModifyAddressHandler(BaseHandler):
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
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('phone') or not params.get('address') or not params.get('realName'):
            return self.write_json(error.DATA_BROKEN)

        count = player_model.edit_address(self.share_db(), database.escape(params.get('address')),
                                          database.escape(params.get('realName')),
                                          database.escape(params.get('phone')), self.uid)
        if count == 0:
            return self.write_json(error.DATA_BROKEN)
        return self.write_json(error.OK)


class BuyScoreItemHandler(BaseHandler):
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
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('itemId'):
            return self.write_json(error.DATA_BROKEN)

        item = money_model.get_item_by_id(self.share_db(), params.get('itemId'))
        if not item or item['Configid'] != 4:
            return self.write_json(error.DATA_BROKEN)

        address = player_model.get_address(self.share_db(), self.uid)
        if not address:
            return self.write_json(error.DATA_BROKEN)

        player = player_model.get_by_uid(self.share_db(), self.uid)
        item_score = int(item['Prices'])
        if player['score'] < item_score:
            return self.write_json(error.SCORE_ERROR)

        exchange_count = money_model.get_exchanged_item_count(self.share_db(), self.uid, item['Id'])
        # 超出兑换次数限制
        if exchange_count >= item['LimitCount']:
            return self.write_json(error.LIMITION_ERROR)

        count = player_model.update_player_score_with_reason(self.share_db(), self.share_db_logs(), self.uid,
                                                             -item_score, const.REASON_GAME_SCORE_BUY_ITEM)
        # item_score有可能为0
#        if count == 0:
#            return self.write_json(error.SCORE_ERROR)

        status = 0
        # 直接兑换钻石
        if item['Isservice'] == 1:
            player = player_model.get_by_uid(self.share_db(), self.uid)
            left_diamonds = player.get('diamond', 0)
            status = 1
            player_model.add_diamonds_with_log(self.share_db(), self.share_db_logs(), self.uid, item['Numbers'],
                                               0, "", const.REASON_EXCHANGE, left_diamonds)

        integral_num = '{0}{1}'.format(
            datetime.fromtimestamp(time.time(), tz=timezone('Asia/Shanghai')).strftime('%Y%m%d%H%M%S'),
            random.randint(1000, 10000)
        )
        money_model.insert_score_item(self.share_db(), integral_num, item['Id'], self.uid,
                                      address['phone'], item_score, address['real_name'], address['address'], status)

        # 返回成功
        return self.write_json(error.OK)


class BuyYuanBaoHandler(BaseHandler):
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
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('count'):
            return self.write_json(error.DATA_BROKEN)

        count = params['count']
        player_model.add_yuan_bao(self.share_db(), self.uid, count)
        if count == 0:
            return self.write_json(error.SCORE_ERROR)

        return self.write_json(error.OK, {"yuan_bao": count})
