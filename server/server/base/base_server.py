# coding:utf-8

from base import logs
from base.commands_s2s import S2S_SEND, S2S_HEART_BEAT, S2S_ACK
from protocol import protocol_utils
from protocol.route_client import connect_route_server
from utils.singleton import Singleton
from models import database

import traceback
from schema import SchemaError
from utils import utils


class BaseServer(metaclass=Singleton):

    def __init__(self):
        self._commands = {}
        self._checker = {}
        self.__route_client = None
        self.__cid = 1  # 当前命令序号
        self.__message_callback = None
        self.__logger = None

        self._server_id = 0  # 服务器ID
        self._service_type = 0
        self._service_name = ""
        self._service_info = None
        self.__configs = None

    @property
    def configs(self):
        if not self.__configs:
            self.__configs = database.get_all_configs()
        return self.__configs

    @property
    def sid(self):
        return self.server_id

    @property
    def logger(self):
        if not self.__logger:
            self.__logger = logs.make_logger(self.service_name, self.server_id)
        return self.__logger

    def setup(self, server_id, service_type, service_name, server_info):
        assert server_id > 0
        self._server_id = server_id
        self._service_type = service_type
        self._service_name = service_name
        self._service_info = server_info

    @property
    def server_id(self):
        return self._server_id

    @property
    def service_type(self):
        return self._service_type

    @property
    def service_name(self):
        return self._service_name

    def _add_handler(self, cmd, func):
        assert cmd and cmd > 0 and func
        #assert self._commands.get(cmd) is None, "duplicate handler"
        self._commands[cmd] = func

    def _add_handlers(self, cmd_handlers):
        for k, v in list(cmd_handlers.items()):
            self._add_handler(k, v)

    def service(self, cmd, uid, data):
        func = self._commands.get(cmd)
        if not func or not callable(func):
            print("cmd not bind aaa: ", self.__class__.__name__, cmd)
            return

        func(uid, data)

    def _check_data(self, cmd, direction: str, data):
        if cmd not in self._checker:
            return data

        if direction not in self._checker[cmd]:
            return dict()

        try:
            data = self._checker[cmd][direction].validate(data)
        except SchemaError as e:
            self.__logger.warn("command : " + str(cmd) + "\ndirector is:" + str(direction) + "\n" + str(e))
            raise e

        return data

    def _check_in_data(self, cmd, data):
        return self._check_data(cmd, "IN", data)

    def _check_out_data(self, cmd, data):
        return self._check_data(cmd, "OUT", data)

    def _set_checker(self, checker: dict):
        self._checker = checker

    def _start_listen_channel(self, callback):
        assert callback
        self.__message_callback = callback
        self.__init_listen_client()

    def _stop_listen_channel(self):
        self.__clear_route_client()

    def __clear_route_client(self):
        if self.__route_client:
            self.__route_client.close()
            self.__route_client = None

    def __on_connect_error(self, err):
        self.logger.error("__on_connect_error: %s", str(err))
        self.__init_listen_client()

    def __on_connect_success(self, client):
        self.logger.info("__on_connect_success %s", str(client))
        self.__route_client = client
        self.__route_client.set_handlers(self.__on_connection_lost, self.__on_line_received)
        self._s2s_heart_beat(0)

    def __on_connection_lost(self, client):
        self.logger.error("connection lost: %s", str(client))
        self.__init_listen_client()

    def __on_line_received(self, client, line):
        self.logger.debug("%s receive: %s", self.service_name, line)
        head, body = protocol_utils.unpack_s2s_package(line)
        if not head or type(head) is not list:
            return

        cid, from_sid, from_service, to_sid, to_service, with_ack, cmd = protocol_utils.unpack_s2s_head(head)

        if cmd == S2S_HEART_BEAT:
            return
        if cmd == S2S_ACK:
            return
        if cmd == S2S_SEND:
            try:
                self.__message_callback(from_sid, from_service, to_sid, to_service, body)
            except Exception as data:
                print(str(data) + "\n" + str(traceback.format_exc()))
                self.logger.error("message callback error: %s %s %s", str(data), str(client),
                                  str(traceback.format_exc()))

                line = traceback.format_exc().splitlines()
                msg = "\n".join(line[-5::1])
                error = f"{self._service_name}-{self._server_id}\n{utils.read_version()}\n\n{msg}"
                database.share_redis_game().publish('exceptions', error)

    def __init_listen_client(self):
        self.logger.info("__init_listen_client")
        self.__clear_route_client()
        connect_route_server(self.__on_connect_success, self.__on_connect_error)

    def _s2s_send(self, to_sid, to_service, with_ack, body):
        return self._s2s_publish(to_sid, to_service, with_ack, S2S_SEND, body)

    def _s2s_raw_send(self, from_sid, from_service, to_sid, to_service, with_ack, body):
        return self._s2s_raw_publish(0, from_sid, from_service, to_sid, to_service, with_ack, S2S_SEND, body)

    def _s2s_heart_beat(self, with_ack):
        return self._s2s_publish(0, 0, with_ack, S2S_HEART_BEAT, "")

    def _s2s_raw_publish(self, cid, from_sid, from_service, to_sid, to_service, with_ack, cmd, body):
        head = self._pack_s2s_head(cid, from_sid, from_service, to_sid, to_service, with_ack, cmd)
        obj = [head, body]
        return self._do_s2s_raw_publish(obj)

    def _s2s_publish(self, to_sid, to_service, with_ack, cmd, body):
        obj = self._pack_s2s_package(to_sid, to_service, with_ack, cmd, body)
        return self._do_s2s_raw_publish(obj)

    def _do_s2s_raw_publish(self, obj):
        #self.logger.debug("%s publish: %d %s", self.service_name, self.server_id, str(obj))
        if not self.__route_client or not self.__route_client.is_connected:
            # self.logger.warn("_do_s2s_raw_publish without client")
            return
        try:
            self.__route_client.send(obj)
        except Exception as data:
            self.logger.warn("_publish_raw_object with exception: %d %s", self.server_id, str(data))
            return

    def make_cid(self):
        cid = self.__cid
        self.__cid += 1
        return cid

    def _pack_s2s_head(self, cid, from_sid, from_service, to_sid, to_service, with_ack, cmd):
        cid = cid or self.make_cid()
        from_sid = from_sid or self.sid
        from_service = from_service or self.service_type
        return [cid, from_sid, from_service, to_sid, to_service, with_ack, cmd]

    def _pack_s2s_package(self, to_sid, to_service, with_ack, cmd, body):
        head = self._pack_s2s_head(0, 0, 0, to_sid, to_service, with_ack, cmd)
        return [head, body]
