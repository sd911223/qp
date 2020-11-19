# coding:utf-8

from configs import error, const
from .base_handler import BaseHandler
from models import channel_configs
from models import player_model
from utils import utils


class ShareDiamondHandler(BaseHandler):
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
        # 配置是否开启
        yao_you_de_zuan_2 = channel_configs.get_by_key(self.share_db(), 0, 0, 'yao_you_de_zuan_2')
        if not yao_you_de_zuan_2:
            return self.write_json(error.ACCESS_DENNY)

        user = player_model.get_by_uid(self.share_db(), self.uid)
        if not user:
            return self.write_json(error.UID_ERROR)

        if user.get('share_time') != 0:
            return self.write_json(error.ACCESS_DENNY)

        # 修改用户分享时间
        player_model.set_share_time(self.share_db(), self.uid)

        # 赠送钻石区分代理及玩家 & 写入记录
        diamond = 10
        left_diamonds = user.get('diamond', 0)
        player_model.add_diamonds_with_log(self.share_db(), self.share_db_logs(), self.uid, diamond, "0", "",
                                           const.REASON_SHARE, left_diamonds + diamond)
        return self.write_json(error.OK, {"diamond": diamond})


class ShareDiamondEveryDayHandler(BaseHandler):
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
        # 配置是否开启
        yao_you_de_zuan_3 = channel_configs.get_by_key(self.share_db(), 0, 0, 'yao_you_de_zuan_3')
        if not yao_you_de_zuan_3:
            return self.write_json(error.ACCESS_DENNY)

        user = player_model.get_by_uid(self.share_db(), self.uid)
        if not user:
            return self.write_json(error.UID_ERROR)

        if user.get('share_time') >= utils.timestamp_today():
            return self.write_json(error.ACCESS_DENNY)

        # 修改用户分享时间
        player_model.set_share_time(self.share_db(), self.uid)

        # 写入记录
        diamond = 8
        left_diamonds = user.get('diamond', 0)
        player_model.add_diamonds_with_log(self.share_db(), self.share_db_logs(), self.uid, diamond, "0", "",
                                           const.REASON_SHARE, left_diamonds + diamond)
        return self.write_json(error.OK, {"diamond": diamond})
