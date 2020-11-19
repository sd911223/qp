# coding:utf-8

from configs import error

from .base_handler import BaseHandler
from utils import utils
from models import player_model


class QueryUidHandler(BaseHandler):
    """查询UID是否存在"""

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
        if not params or not params.get('uid'):
            return self.write_json(error.DATA_BROKEN)

        uid = int(params.get('uid'))
        if uid <= 0:
            return self.write_json(error.DATA_BROKEN)

        if not self.share_db():
            return self.write_json(error.SYSTEM_ERR)

        info = player_model.get_by_uid(self.share_db(), uid)
        if info and info.get('uid', 0) > 0:
            diamond = info.get('diamond', 0)
            nick_name = player_model.get_nick_name(info)
            return self.write_json(error.OK, {"exist": True, "nickName": nick_name, 'avatar': info.get('avatar', ''),
                                              "diamond": diamond, "uid": info.get('uid', 0)})
        else:
            info = player_model.get_by_uid1(self.share_db(), uid)
            if info and info.get('uid', 0) > 0:
                diamond = info.get('diamond', 0)
                nick_name = player_model.get_nick_name(info)
                head = 'http://39.101.163.242:8194/static/ps/%d.png' % uid
                return self.write_json(error.OK, {"exist": True, "nickName": nick_name, 'avatar': head,
                                                  "diamond": diamond, "uid": info.get('uid', 0)})
        return self.write_json(error.OK, {"exist": False})
