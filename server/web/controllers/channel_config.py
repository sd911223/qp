# coding:utf-8

from configs import error

from .base_handler import BaseHandler
from models import channel_configs


class ChannelConfigHandler(BaseHandler):

    def prepare(self):
        if not self.check_fixed_params(False):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign_no_token():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        """
        获得渠道配置信息，按以下顺序进行覆盖: (全平台、全渠道)->(单平台、全渠道)->(单平台、单渠道)
        :return:
        """
        if not self.share_db():
            return self.write_error(error.SYSTEM_ERR)

        result = channel_configs.get(self.share_db(), self.platform, self.channel_id)
        return self.write_json(error.OK, result)
