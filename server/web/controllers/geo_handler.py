# coding:utf-8
from configs import error

from .base_handler import BaseHandler
from models import report_model
from utils import utils


class UploadGeoHandler(BaseHandler):
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
        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('str'):
            return self.write_json(error.DATA_BROKEN)

        uid = int(self.get_int('uid'))
        loc = params.get('str').split(',')

        x = float(loc[0])
        y = float(loc[1])
        report_model.insert_geo_information(self.share_db_logs(), uid, x, y)
        return self.write_json(error.OK, {})
