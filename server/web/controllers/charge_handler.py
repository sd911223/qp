# coding:utf-8

from configs import error
from .base_handler import BaseHandler


class ChargePushHandler(BaseHandler):
    def prepare(self):
        pass

    def get(self):
        self.broad_cast_user([self.get_int("uid")],
                             {"type": 88, "count": self.get_int("count"), "chargeType": self.get_int('type')})
        return self.write_json(error.OK)
