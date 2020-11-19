# coding:utf-8

from configs import error
from models import online_model, tables_model, feedback_models
from models import player_model, diamond_price_model
from utils import utils
from .base_handler import BaseHandler


class DiamondsHandler(BaseHandler):
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
        player_info = player_model.get_by_uid(self.share_db(), self.uid)
        if not player_info:
            return

        idle_table_diamond = tables_model.get_total_idle_diamonds_by_uid(self.share_db(), self.uid)
        calc_diamond = int(player_info['diamond'] - idle_table_diamond)
        show_diamonds = max(0, calc_diamond)

        idle_match_table_diamond = tables_model.get_total_match_idle_diamonds_by_uid(self.share_db(), self.uid)
        show_la_jiao_dou = max(0, int(player_info['la_jiao_dou'] - idle_match_table_diamond))

        show_yuan_bao = player_info['yuan_bao']
        if calc_diamond < 0:
            show_yuan_bao = max(0, player_info['yuan_bao'] + calc_diamond)

        result = {
            "diamond": utils.str_to_int(show_diamonds),
            "laJiaoDou": show_la_jiao_dou,
            "yuanBao": show_yuan_bao,
            "score": int(player_info['score']),
            "detail": [],
        }
        return self.write_json(error.OK, result)


class DiamondPriceHandler(BaseHandler):
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
        data = {"data": []}
        price = diamond_price_model.get_all_diamonds_price()
        if len(price) > 0:
            data['data'] = price
        return self.write_json(error.OK, data)


class RefreshHandler(BaseHandler):
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
        if not self.share_db():
            return self.write_json(error.SYSTEM_ERR)

        result = {"refreshSuccess": online_model.fresh_online(self.share_db(), self.uid) > 0}
        return self.write_json(error.OK, result)


class FeedBackHandler(BaseHandler):
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
        if not params or not params.get('phone') or not params.get('content'):
            return self.write_json(error.DATA_BROKEN)

        now = utils.timestamp()
        count = feedback_models.insert_feedback(self.share_db(), self.uid, params.get('phone'), params.get('content'),
                                                now)
        if count == 0:
            return self.write_json(error.DATA_BROKEN)
        return self.write_json(error.OK)
