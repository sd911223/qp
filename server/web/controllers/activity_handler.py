# coding:utf-8

from configs import error
from models import activity_model
from models import player_model
from utils import utils
from .base_handler import BaseHandler

DIAMOND = 1
GOLD = 2
LA_JIAO = 3
JI_FEN = 4


class SignInActivity(BaseHandler):
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
        player = player_model.get_by_uid(self.share_db(), self.uid)
        if not player:
            return self.write_json(error.DATA_BROKEN)

        sign_count = player['sign_count']
        sign_time = player['sign_time']

        if sign_time >= utils.timestamp_today():
            return self.write_json(error.SIGN_DAY_ERROR)

        #如果两次签到日期没有连续则重新开始连续签到计算
        if sign_time < utils.timestamp_yesterday():
            sign_count = 0

        now_time = utils.timestamp()
        now_count = sign_count + 1
        if now_count == 8:
            now_count = 1

        player_model.update_player_sign_time_and_count(self.share_db(), self.uid, now_time, now_count)

        info = activity_model.get_sign_bonus_by_day(self.share_db(), now_count)
        if not info:
            return self.write_json(error.DATA_BROKEN)

        item_type = info['item_type']
        item_count = info['item_count']

        if item_type == DIAMOND:
            player_model.add_diamonds(self.share_db(), self.uid, item_count)
        elif item_type == GOLD:
            pass
        elif item_type == LA_JIAO:
            player_model.add_la_jiao_dou(self.share_db(), self.uid, item_count)
        elif item_type == JI_FEN:
            player_model.add_score(self.share_db(), self.uid, item_count)

        return self.write_json(error.OK, info)


class SignInItemInfo(BaseHandler):
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
        info = activity_model.query_sign_bonus(self.share_db())
        return self.write_json(error.OK, info)


class SpringActivity(BaseHandler):
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
        data = activity_model.get_spring_activity_status(self.share_db(), self.uid)
        if not data:
            return self.write_json(error.SYSTEM_ERR)
        can_recv_game_bonus = (data['last_game_time'] >= utils.timestamp_today() and data[
            'game_bonus_time'] < utils.timestamp_today())
        data['can_recv_game_bonus'] = can_recv_game_bonus
        data.pop('last_game_time', None)
        data.pop('game_bonus_time', None)
        return self.write_json(error.OK, data)


class SpringActivityLogs(BaseHandler):
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
        info = activity_model.query_spring_activity_logs(self.share_db_logs(), self.uid)
        return self.write_json(error.OK, info)


class SpringActivityRecv(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    # key, val, symbol, limit, score, valid_key, item_bonus_key, item_bonus_val

    def __make_item_2_config(self):
        # 游戏奖励
        return 0, utils.timestamp(), 0, 0, 0, 0, "score", 30

    def __make_item_3_config(self):
        # 礼包1奖励
        valid_key = key = 'item_1_status'
        return key, 1, '=', 0, 8, valid_key, "score", 288

    def __make_item_4_config(self):
        # 礼包2奖励
        valid_key = key = 'item_2_status'
        return key, 1, '=', 0, 88, valid_key, "diamond", 188

    def __make_item_5_config(self):
        # 礼包3奖励
        valid_key = key = 'item_3_status'
        return key, 1, '=', 0, 188, valid_key, "score", 588

    def __make_item_6_config(self):
        # 礼包4奖励
        valid_key = key = 'item_4_status'
        return key, 1, '=', 0, 288, valid_key, "diamond", 288

    def __make_item_7_config(self):
        # 礼包5奖励
        valid_key = key = 'item_5_status'
        return key, 1, '=', 0, 1588, valid_key, "diamond", 888

    def __make_modify_data(self, item_id):
        if item_id == 2:
            return self.__make_item_2_config()
        if item_id == 3:
            return self.__make_item_3_config()
        if item_id == 4:
            return self.__make_item_4_config()
        if item_id == 5:
            return self.__make_item_5_config()
        if item_id == 6:
            return self.__make_item_6_config()
        if item_id == 7:
            return self.__make_item_7_config()

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "itemID" not in params:
            return self.write_json(error.DATA_BROKEN)
        item_id = int(params.get('itemID'))
        if item_id <= 1 or item_id > 7:
            return self.write_json(error.DATA_BROKEN)
        key, val, symbol, limit, score, valid_key, item_bonus_key, item_bonus_val = self.__make_modify_data(item_id)
        if item_id in (3, 4, 5, 6, 7,):
            status = activity_model.modify_spring_activity_user_status(self.share_db(), self.uid, key, val, valid_key,
                                                                       symbol, limit, score)
        else:
            status = activity_model.modify_spring_activity_user_game_status(self.share_db(), self.uid)
        if status != 1:
            return self.write_json(error.DATA_BROKEN)
        activity_model.insert_spring_activity_log(self.share_db_logs(), self.uid, item_id)
        activity_model.modify_player_info(self.share_db(), self.uid, item_bonus_key, item_bonus_val)
        return self.write_json(error.OK, {"itemID": item_id, "retType": item_bonus_key, "retCount": item_bonus_val})
