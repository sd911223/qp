# coding:utf-8

from utils import utils
from utils.logs import gate_logger
from twisted.protocols import basic
import zlib

basic.LineOnlyReceiver.MAX_LENGTH = 8192


class SessionClient(basic.LineOnlyReceiver):

    def __init__(self):
        basic.LineOnlyReceiver.__init__(self)
        self.__is_clean = False  # 是否是清理的标志
        self.__uid = 0  # 此session所属玩家ID
        self.__last_data_arrive_time = utils.timestamp()
        self.__verified = False
        self.__ip = ""

    @property
    def ip(self):
        return self.__ip

    @property
    def last_data_time(self):
        return self.__last_data_arrive_time

    @property
    def uid(self):
        return self.__uid

    @property
    def verified(self):
        return self.__verified

    def connectionMade(self):
        """ 连接建立事件 """
        from hall.gateway import Gateway
        Gateway.share_server().on_player_connection_made(self)
        self.__ip = self.transport.client[0]

    def __on_close(self):
        self.__uid = 0
        self.__verified = False
        self.__ip = ""

    def connectionLost(self, reason=""):
        print('connectionLost')
        if not self.__is_clean:  # 清理session时不触发断线的流程和操作
            from hall.gateway import Gateway
            Gateway.share_server().on_player_connection_lost(self)

        self.__on_close()

    def lineReceived(self, line):
        self.__last_data_arrive_time = utils.timestamp()
        from hall.gateway import Gateway
        Gateway.share_server().on_line_received(self, line)

    #  当接收到的一行长度超过了最大值时的错误响应，并断开连接
    def lineLengthExceeded(self, line):
        gate_logger.warn("line receive too long: %s, len: %d", self.ip, len(line))
        basic.LineOnlyReceiver.lineLengthExceeded(self, line)
        self.close()

    def set_verified(self, uid, flag):
        assert uid > 0
        self.__verified = flag
        self.__uid = uid
        if flag:
            self.__on_connection_verified()

    """ 连接认证通过时的调用 """

    def __on_connection_verified(self):
        from hall.gateway import Gateway
        Gateway.share_server().on_session_auth_success(self)

    # 发送数据包, obj要可以被json编码
    def send(self, obj):
        s = utils.json_encode(obj).encode("utf-8")
        # message = zlib.compress(s)
        message = s
        self.sendLine(message)

    # 发送字符串
    def send_string(self, string):
        self.sendLine(string)

    # 清理此session，先设置标志并关闭连接
    def clear(self):
        self.__is_clean = True
        self.close()

    # 关闭连接的方法
    def close(self):
        self.__on_close()
        if self.transport:
            self.transport.loseConnection()
        self.transport = None
