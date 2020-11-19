# coding:utf-8
from base import const
from base.init import start

if __name__ == '__main__':
    from hall.gateway import Gateway

    start(Gateway, const.SERVICE_GATE, __file__[0:-3], True)
