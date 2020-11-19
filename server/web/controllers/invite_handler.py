# coding:utf-8

from configs import error, const

from .base_handler import BaseHandler
from utils import utils
from models import share_config_model, invite_model, player_model, share_logs_model
import uuid
import requests
import time
import ujson as json


class InviteFriendListHandler(BaseHandler):
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
        config = share_config_model.get_all_configs(self.share_db())
        a_start_time = 0
        a_end_time = 0

        for i in config:
            if i['var'] == 'z_activity_start_time':
                a_start_time = int(i['value'])
            elif i['var'] == 'z_activity_end_time':
                a_end_time = int(i['value'])
        data = invite_model.get_all_refer_players(self.share_db(), self.uid)
        r_data = []
        for i in data:
            round_count = invite_model.get_player_play_count(self.share_db_logs(), i['uid'], i['refer_time'],
                                                             a_start_time, a_end_time)
            if not round_count['round_count']:
                i['round_count'] = 0
            else:
                i['round_count'] = int(str(round_count['round_count']))
            r_data.append(i)

        return self.write_json(error.OK, r_data)


class WithdrawRecordsHandler(BaseHandler):

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
        params = dict()
        params['uid'] = self.uid
        params['time'] = time.strftime("%Y-%m-%d %X", time.localtime())
        params['client_ip'] = self.request.remote_ip
        params['key'] = const.KEY
        params['sign'] = self.make_sign(params)

        r = requests.post(const.GET_CODE_LIST_URL, data=params)
        data = {}
        if r.status_code is 200:
            data = json.loads(r.text)
        return self.write_json(error.OK, data)


class InviteActivityConfigHandler(BaseHandler):

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
        data = share_config_model.get_all_config_items(self.share_db())
        start_time = utils.timestamp_today()
        end_time = utils.timestamp_tomorrow() - 1
        player = player_model.get_by_uid(self.share_db(), self.uid)
        res = invite_model.get_withdraw_count_by_unionid(self.share_db_logs(), start_time, end_time,
                                                         player['unionid'])
        if res and 'count' in res:
            data['owner_withdraw_count'] = res['count']

        return self.write_json(error.OK, data)


class ExchangeHandler(BaseHandler):

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
        data = share_config_model.get_all_configs(self.share_db())
        a_start_time = 0
        a_end_time = 0
        max_round_count = 1000
        exchange_diamond = 0
        for i in data:
            if i['var'] == 'max_round_count':
                max_round_count = int(i['value'])
            elif i['var'] == 'diamond':
                exchange_diamond = int(i['value'])
            elif i['var'] == 'z_activity_start_time':
                a_start_time = int(i['value'])
            elif i['var'] == 'z_activity_end_time':
                a_end_time = int(i['value'])

        players = invite_model.get_exchange_or_withdraw_uids(self.share_db(), self.uid, max_round_count,
                                                             a_start_time, a_end_time)

        if len(players) == 0:
            return self.write_error(error.REFER_USER_ERROR)

        uids = []
        for i in players:
            uids.append(str(i['uid']))

        exchange_diamond = len(players) * exchange_diamond
        player = player_model.get_by_uid(self.share_db(), self.uid)

        left_diamonds = player.get('diamond', 0)
        total_diamonds = left_diamonds + exchange_diamond
        player_model.add_diamonds_with_log(self.share_db(), self.share_db_logs(), self.uid, exchange_diamond,
                                           0, "", const.REASON_EXCHANGE, total_diamonds)

        share_logs_model.add_share_logs_count(self.share_db_logs(), player['unionid'], 4, exchange_diamond)
        invite_model.modify_players_withdraw_time(self.share_db(), uids)
        data = {"diamond": exchange_diamond}
        return self.write_json(error.OK, data)


class WithdrawHandler(BaseHandler):

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
        data = share_config_model.get_all_configs(self.share_db())
        a_start_time = 0
        a_end_time = 0
        max_round_count = 1000
        money = 0
        least_withdraw_money = 0
        can_withdraw_count = 0
        max_withdraw = 0

        for i in data:
            if i['var'] == 'max_round_count':
                max_round_count = int(i['value'])
            elif i['var'] == 'money':
                money = int(i['value'])
            elif i['var'] == 'least_withdraw_money':
                least_withdraw_money = int(i['value'])
            elif i['var'] == 'can_withdraw_count':
                can_withdraw_count = int(i['value'])
            elif i['var'] == 'z_activity_start_time':
                a_start_time = int(i['value'])
            elif i['var'] == 'z_activity_end_time':
                a_end_time = int(i['value'])
            elif i['var'] == 'max_withdraw':
                max_withdraw = int(i['value'])

        start_time = utils.timestamp_today()
        end_time = utils.timestamp_tomorrow() - 1

        today_withdraw_money = invite_model.get_today_withdraw_money(self.share_db_logs(), start_time, end_time)
        if not today_withdraw_money['amount']:
            today_withdraw_money['amount'] = 0
        if int(str(today_withdraw_money['amount'])) / 100 >= max_withdraw:
            return self.write_error(error.OVER_GLOBAL_MAX_WITHDRAW)

        players = invite_model.get_exchange_or_withdraw_uids(self.share_db(), self.uid, max_round_count,
                                                             a_start_time, a_end_time)
        if len(players) == 0:
            return self.write_error(error.REFER_USER_ERROR)

        uids = []
        for i in players:
            uids.append(str(i['uid']))

        player = player_model.get_by_uid(self.share_db(), self.uid)
        res = invite_model.get_withdraw_count_by_unionid(self.share_db_logs(), start_time, end_time,
                                                         player['unionid'])
        if res and 'count' in res:
            if int(res['count']) >= can_withdraw_count:
                return self.write_error(error.MAX_WITHDRAW_COUNT)

        money = len(players) * money * 100
        if money < least_withdraw_money * 100:
            return self.write_error(-1)

        params = dict()
        params['uid'] = self.uid
        params['nick_name'] = player['nick_name'] or 'nomobile'
        params['time'] = time.strftime("%Y-%m-%d %X", time.localtime())
        params['serial_number'] = str(uuid.uuid4())
        params['client_ip'] = self.request.remote_ip
        params['money'] = money
        params['key'] = const.KEY
        params['sign'] = self.make_sign(params)
        r = requests.post(const.GET_CODE_URL, data=params)
        data = {}
        if r.status_code is 200:
            data = json.loads(r.text)
            if data['data']['code'] is not "":
                data['data']['money'] = money
                invite_model.modify_players_withdraw_time(self.share_db(), uids)
                share_logs_model.add_share_logs_count(self.share_db_logs(), player['unionid'], 1, money)
        return self.write_json(error.OK, data)


class ShareInviteHandler(BaseHandler):
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
        union_id = player_model.get_by_uid(self.share_db(), self.uid)['unionid']
        share_logs_model.add_share_logs_count(self.share_db_logs(), union_id)
        return self.write_json(error.OK, {})


class QRCodeHandler(BaseHandler):
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
        data = player_model.get_qr_code(self.share_db(), self.uid)
        return self.write_json(error.OK, data)
