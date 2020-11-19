# coding:utf-8
from base import const
from base.init import start_router

if __name__ == '__main__':
    from hall.router import Router

    start_router(Router, const.SERVICE_PUB_SUB, __file__[0:-3])
