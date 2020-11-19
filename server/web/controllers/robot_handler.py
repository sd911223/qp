# coding:utf-8

from configs import error

from .base_handler import BaseHandler
from utils import utils
from models import activity_model


class RobotRoomsHandler(BaseHandler):

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

        open_room_min = 0
        start_time = params.get('startTime')
        end_time = params.get('endTime')
        data = activity_model.get_robot_rooms(self.share_db_logs(), start_time, end_time, open_room_min, uid)
        if data and len(data) > 0:
            return self.write_json(error.OK, data)
        return self.write_json(error.OK)
