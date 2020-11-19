# coding:utf-8

from configs import error, const
from .base_handler import BaseHandler
from models import channel_configs
from models import player_model


class LoginDiamondHandler(BaseHandler):
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
        zha_shen_gui_wei = channel_configs.get_by_key(self.share_db(), 0, 0, 'zha_shen_gui_wei')
        if not zha_shen_gui_wei:
            return self.write_json(error.ACCESS_DENNY)

        user = player_model.get_by_uid(self.share_db(), self.uid)
        if not user:
            return self.write_json(error.UID_ERROR)

        diamond = user.get('get_diamond')
        if diamond == 0 or diamond == -1:
            return self.write_json(error.ACCESS_DENNY)

        player_model.set_get_diamond(self.share_db(), self.uid, -1)

        # 赠送钻石 & 写入记录
        left_diamonds = user.get('diamond', 0)
        player_model.add_diamonds_with_log(self.share_db(), self.share_db_logs(), self.uid, diamond, "0", "",
                                           const.REASON_GUI_WEI, left_diamonds + diamond)
        return self.write_json(error.OK)
