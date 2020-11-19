# coding:utf-8

from configs import error

from .base_handler import BaseHandler
from models import version_model


class CheckUpdateHandler(BaseHandler):

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
        has_new = False
        detail = {}
        versions = version_model.get_versions(self.share_db(), self.platform, self.channel_id)
        if versions:
            for version in versions:
                if version.version <= self.ver:
                    continue
                has_new = True
                detail = {"isForce": version.is_force > 0, "readme": version.desc, "url": version.update_url}
                if version.channel_id > 0:
                    break
        result = {"hasNewVersion": has_new, "detail": detail}
        return self.write_json(error.OK, result)
