# coding:utf-8
from configs import error
from .base_handler import BaseHandler
from models import base_redis
from utils import utils


class DumpRecordHandler(BaseHandler):
    def prepare(self):
        pass

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    @staticmethod
    def __get_round_details_in_redis(round_id):
        if not round_id:
            return []
        all_data = base_redis.get_all_play_details()
        if not all_data:
            return []
        for item in all_data:
            data = utils.json_decode(item)
            if not data:
                continue
            if data.get('round_id', 0) == round_id:
                return data.get('commands')
        return []

    def _request(self):
        round_id = self.get_int('round_id')
        details = self.__get_round_details_in_redis(round_id)
        return self.write_json(error.OK, {"details": details})
