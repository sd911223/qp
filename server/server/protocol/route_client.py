# coding:utf-8
from twisted.internet import reactor
from twisted.protocols import basic
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet import protocol

from configs import config
from utils import utils
from base.logs import main_logger


class PubClient(basic.LineOnlyReceiver):

    def __init__(self):
        basic.LineOnlyReceiver.__init__(self)
        self.__last_data_arrive_time = utils.timestamp()
        self.__on_connection_lost = None
        self.__on_line_received = None
        self.__is_connected = False

    @property
    def is_connected(self):
        return self.__is_connected

    @property
    def last_data_time(self):
        return self.__last_data_arrive_time

    def set_handlers(self, on_connection_lost, on_line_received):
        self.__on_connection_lost = on_connection_lost
        self.__on_line_received = on_line_received

    def connectionMade(self):
        """ 连接建立事件 """
        self.__is_connected = True
        print('python senc bround cast')

    def connectionLost(self, reason=""):
        self.__is_connected = False
        if callable(self.__on_connection_lost):
            self.__on_connection_lost(self)
        else:
            main_logger.warn("connection lost with no handlers!")
        self.__on_close()

    def __on_close(self):
        self.__on_connection_lost = None
        self.__on_line_received = None
        self.transport = None

    def lineReceived(self, line):
        self.__last_data_arrive_time = utils.timestamp()
        if callable(self.__on_line_received):
            self.__on_line_received(self, line)
        else:
            main_logger.warn("line receive with no handlers!", line)

    def lineLengthExceeded(self, line):
        main_logger.warn("line receive too long: %s, len: %d", self.ip, len(line))

    def send(self, obj):
        # 发送数据包, obj要可以被json编码
        # s = utils.json_encode(obj)
        self.sendLine(utils.json_encode(obj).encode("utf8"))

    # 关闭连接的方法
    def close(self):
        self.__is_connected = False
        if self.transport:
            self.transport.loseConnection()
        self.__on_close()


class PubClientFactory(protocol.Factory):

    def __init__(self):
        pass

    def buildProtocol(self, address):
        return PubClient()


def connect_route_server(on_conn_success, on_conn_fail):
    host = config.get_item("router_ip") or "127.0.0.1"
    port = config.get_item("router_port") or 20000
    point = TCP4ClientEndpoint(reactor, host, port)
    conn = point.connect(PubClientFactory())
    conn.addCallbacks(on_conn_success, on_conn_fail)
