from base import error
from protocol import protocol_utils
from utils.singleton import Singleton


class BaseService(metaclass=Singleton):
    def __init__(self, service_type):
        assert service_type > 0
        self.__service_type = service_type
        self._commands = {}

    @property
    def service_type(self):
        assert self.__service_type > 0
        return self.__service_type

    def _add_handler(self, cmd, func):
        assert cmd and cmd > 0 and func
        assert self._commands.get(cmd) is None, "duplicate handler"
        self._commands[cmd] = func

    def _add_handlers(self, cmd_handlers):
        for k, v in list(cmd_handlers.items()):
            self._add_handler(k, v)

    def service_broad(self, service_type, cmd, data, uid):
        func = self._commands.get(cmd)
        if not func or not callable(func):
            print("cmd not bind aaa: ", cmd)
            return
        func(service_type, cmd, data, uid)

    def service(self, session, cmd, data):
        func = self._commands.get(cmd)
        if not func or not callable(func):
            print("cmd not bind bbb: ", self.__service_type, cmd)
            return
        func(session, data)

    def packet(self, cmd, data=None, code=error.OK):
        body = protocol_utils.pack_client_body(data, code)
        return protocol_utils.pack_client_message(self.__service_type, cmd, body)

    def response(self, session, cmd, data=None, code=error.OK):
        session.send(self.packet(cmd, data, code))

    def response_ok(self, session, cmd, data):
        return self.response(session, cmd, data, error.OK)

    def response_fail(self, session, cmd, code):
        return self.response(session, cmd, None, code)
