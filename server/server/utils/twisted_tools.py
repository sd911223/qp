import time
from twisted.internet import reactor
from twisted.internet import task


class DelayCall(object):

    def __init__(self, seconds, f, *args, **kw):
        self.__timer = reactor.callLater(seconds, f, *args, **kw)

    def cancel(self):
        """取消延时调用
        """
        if not self.__timer:
            return False
        if not self.__timer.active():
            return False
        self.__timer.cancel()

    def left_seconds(self):
        """ 获取计时器的剩余时间 """
        if not self.__timer:
            return 0
        if not self.__timer.active():
            return 0
        return int(round(self.__timer.getTime(), 0) - time.time())


class LoopingCall(object):

    def __init__(self, seconds, f, *args, **kw):
        self.__timer = task.LoopingCall(f, *args, **kw)
        self.__timer.start(seconds)

    def cancel(self):
        """取消定时调用
        """
        if not self.__timer:
            return False
        self.__timer.stop()
