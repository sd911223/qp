# coding:utf-8

import ipaddress
import urllib.parse
import socket
import tornado
import sys

from tornado.options import options
from utils import utils
from models import database
from models import online_model
from configs import config, const, commands_s2s, error
from models import base_redis

from utils import protocol_utils
import tornado.web
import traceback


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        self.uid = 0
        self.game_id = 0
        self.channel_id = 0
        self.ver = ''
        self.platform = 0
        self.script_ver = 0
        self.__conn = None
        self.__conn_logs = None
        self.__configs = None
        self.__redis_conn = None

    def make_sign(self, params):
        keys = list(params.keys())
        keys.sort()
        values = []
        for k in keys:
            values.append(k + '=' + str(params[k]))
        sign_data = "&".join(values)
        return utils.md5(sign_data)

    def share_db(self):
        if self.__conn:
            return self.__conn
        conn = database.connect("db")
        if not conn:
            return None
        self.__conn = conn
        return conn

    @staticmethod
    def __publish_message(obj):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((config.get_by_key('router_ip'), config.get_by_key('router_port')))
        data = utils.json_encode(obj) + "\r\n"
        s.sendall(data.encode('utf-8'))
        s.close()

    def publish(self, cmd, uid, body, service_type):
        message = protocol_utils.pack_to_player_body(cmd, uid, body)
        head = self.__pack_s2s_head(0, 0, service_type, 0, const.SERVICE_GATE, 0, commands_s2s.S2S_SEND)
        obj = [head, message]
        return self.__publish_message(obj)

    def publish_to_service(self, cmd, uid, body, service_type):
        message = protocol_utils.pack_to_player_body(cmd, uid, body)
        head = self.__pack_s2s_head(0, 0, const.SERVICE_WEB, 0, service_type, 0, commands_s2s.S2S_SEND)
        obj = [head, message]
        return self.__publish_message(obj)

    def publish_to_service_with_sid(self, cmd, uid, body, service_type, sid):
        message = protocol_utils.pack_to_player_body(cmd, uid, body)
        head = self.__pack_s2s_head(0, 0, const.SERVICE_WEB, sid, service_type, 0, commands_s2s.S2S_SEND)
        obj = [head, message]
        return self.__publish_message(obj)

    @staticmethod
    def __pack_s2s_head(cid, from_sid, from_service, to_sid, to_service, with_ack, cmd):
        cid = cid or 0
        from_sid = from_sid or 0
        from_service = from_service or 0
        return [cid, from_sid, from_service, to_sid, to_service, with_ack, cmd]

    def broad_cast_user(self, users, data):
        if not users:
            return

        self.publish(7, users, data, const.SERVICE_SYSTEM)

    def share_redis(self):
        if self.__redis_conn:
            return self.__redis_conn
        conn = base_redis.share_connect()
        if not conn:
            return None
        self.__redis_conn = conn
        return conn

    def share_db_logs(self):
        if self.__conn_logs:
            return self.__conn_logs
        conn = database.connect("db_logs")
        if not conn:
            return None
        self.__conn_logs = conn
        return conn

    @property
    def configs(self):
        if not self.__configs:
            self.__configs = base_redis.get_all_configs()
        return self.__configs

    def get_int_ip(self):
        int_ip = 0
        try:
            int_ip = int(ipaddress.ip_address(self.request.remote_ip))
        except ValueError:
            pass
        return int_ip

    # 获得整型参数
    def get_int(self, name):
        try:
            return int(self.get_argument(name, 0))
        except Exception as e:
            print(e)
            return 0

    # 获得字符串参数
    def get_string(self, name):
        return self.get_argument(name, '')

    # 回答客户端
    def write_json(self, status, data=None):
        desc = sys._getframe(1).f_lineno if status != error.OK else ""
        self.write({'status': status, 'desc': desc, 'data': data or []})
        self.finish()
        return

    # 回答客户端
    def write_json1(self, status, data=None):
        desc = sys._getframe(1).f_lineno if status != error.OK else ""
        self.write({'status': status, 'desc': desc, 'data': data or []})
        self.finish()
        return

    def write_error(self, code, desc=None, data=None):
        desc = sys._getframe(1).f_lineno if not desc else desc
        self.write({'status': code, 'desc': desc, 'data': data or []})
        self.finish()
        return

    @property
    def db(self):
        return self.application.db

    @staticmethod
    def _check_sign(params, sign, token=""):
        sign_obj = params.get("sign")
        if not sign_obj:
            return False

        check_sign = sign_obj[0].decode(encoding='UTF-8')
        if not check_sign or len(check_sign) < 1:
            return False

        keys = list(params.keys())
        keys.sort()
        values = []

        for k in keys:
            if k == "sign":
                continue
            tmp_str = params[k][0].decode(encoding='UTF-8')
            values.append(k + '=' + urllib.parse.quote_plus(tmp_str))
        values.append("key={0}".format(sign))
        if token and len(token) > 0:
            values.append("token={0}".format(token))

        sign_data = "&".join(values)
        return utils.md5(sign_data) == check_sign

    def check_sign(self):
        uid = int(self.get_argument("uid"))
        token = online_model.get_token(self.share_db(), uid)
        sign_passed = self._check_sign(self.request.arguments, options.app_sign_key, token)
        if sign_passed:
            self.setup_fixed_params()
        return sign_passed

    def check_sign_no_token(self):
        sign_passed = self._check_sign(self.request.arguments, options.app_sign_key)
        if sign_passed:
            self.setup_fixed_params()
        return sign_passed

    def check_fixed_params(self, with_uid=True):
        if not self.get_argument("uid"):
            return False

        if with_uid and not self.get_int('uid'):
            return False

        if not self.get_int('gameId') or \
                not self.get_int('platform') or \
                not self.get_string("ver") or \
                not self.get_int('channelId') or \
                not self.get_int('time'):
            return False

        return True

    def get_fixed_params(self):
        return {
            'uid': self.get_int('uid'),
            'game_id': self.get_int('gameId'),
            'platform': self.get_int('platform'),
            'ver': self.get_string('ver'),
            'channel_id': self.get_int('channelId'),
            'script_ver': self.get_int('scriptVer')
        }

    def setup_fixed_params(self):
        self.uid = self.get_int('uid') or 0
        self.game_id = self.get_int('gameId')
        self.platform = self.get_int('platform')
        self.channel_id = self.get_int('channelId')
        self.ver = self.get_string('ver')
        self.script_ver = self.get_int('scriptVer')

    def write_error(self, status_code, **kwargs):
        if status_code == 500:
            error_trace_list = traceback.format_exception(*kwargs.get("exc_info"))
            r = ''.join(error_trace_list[-4::1])
            errors = f"{self.request.path}\n{self.uid}\n\n{r}"
            base_redis.share_connect().publish('exceptions', errors)
