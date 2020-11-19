from twisted.internet import protocol
from twisted.protocols import basic
from configs import config
from protocol import protocol_utils
from base import commands_s2s


class RouteProtocol(basic.LineOnlyReceiver):

    def __init__(self, factory, address):
        self.factory = factory
        self.ip = address.host
        self.__sid = 0
        self.__service_type = 0

    @property
    def sid(self):
        return self.__sid

    @property
    def service_type(self):
        return self.__service_type

    def connectionMade(self):
        if self.ip not in self.factory.allow_ips:
            self.sendLine(b"Access denny.")
            self.close()
            return
        self.factory.clients.add(self)

    def connectionLost(self, reason=""):
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        head, body = protocol_utils.unpack_s2s_package(line)
        if not head:
            return
        cid, from_sid, from_service, to_sid, to_service, with_ack, cmd = protocol_utils.unpack_s2s_head(head)
        if 1 == with_ack:  # 响应ACK消息
            self.__response_ack(cid)
        if cmd == commands_s2s.S2S_HEART_BEAT:
            return self.__on_heart_beat(from_sid, from_service)
        if cmd == commands_s2s.S2S_ACK:
            return
        if cmd == commands_s2s.S2S_SEND:
            return self.__try_send_message(to_sid, to_service, line)
        print("unknown cmd: ", cmd)

    def __response_ack(self, cid):
        pass

    def __on_heart_beat(self, from_sid, from_service):
        self.__sid = from_sid
        self.__service_type = from_service

    def __try_send_message(self, to_sid, to_service, line):
        for c in self.factory.clients:
            if c == self:
                continue
            if to_sid > 0 and to_sid != c.sid:
                continue
            if to_service > 0 and to_service != c.service_type:
                continue
            c.sendLine(line)

    def close(self):
        if self.transport:
            self.transport.loseConnection()
        self.transport = None
        self.ip = None


class PubFactory(protocol.Factory):
    def __init__(self):
        self.clients = set()
        self.allow_ips = config.get_item("router_allow_ips") or ["127.0.0.1", "::1"]

    def buildProtocol(self, address):
        return RouteProtocol(self, address)
