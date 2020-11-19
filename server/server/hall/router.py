# coding:utf-8
from twisted.internet import reactor
from twisted.internet import endpoints

from configs import config
from base.base_server import BaseServer
from protocol.route_protocol import PubFactory


class Router(BaseServer):
    def __init__(self):
        BaseServer.__init__(self)
        self.__port = config.get_item("router_port") or 10000  # 端口

    def on_signal_stop(self):  # 收到结束的信号
        return self.__close_server()

    def __close_server(self):
        self.logger.info("start close pubsub server %d ", self.server_id)
        self.logger.info("stop listen channel %d ", self.server_id)

    def start_service(self):  # 启动服务
        endpoints.serverFromString(reactor, "tcp:{0}".format(self.__port)).listen(PubFactory())
        self.logger.info('Starting listening on port %d', self.__port)
        reactor.addSystemEventTrigger('before', 'shutdown', self.on_signal_stop)
        reactor.run()

    @staticmethod
    def share_server():
        return Router()
